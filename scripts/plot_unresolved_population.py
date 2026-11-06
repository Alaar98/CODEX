"""Angular-size diagnostic and illustrative snapshot visibility of every nominal object."""
import csv
import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
from space_debris_detection.optical_validation import OpticalModel, StudyCase, load_baseline, ARCSEC_PER_RAD
from space_debris_detection.plotting import publication_style, save_figure, plt
from space_debris_detection.sensitivity import load_population
from space_debris_detection.snapshot import approximate_sun_direction, classify_snapshot, propagate_population


def main():
    root = Path(__file__).resolve().parents[1]
    source = root/'data/generated/optical'
    manifest = json.loads((source/'manifest.json').read_text())
    case = StudyCase(**manifest['nominal_instrument_case'])
    b = load_baseline(root/'docs/references'/manifest['workbook'])
    model = OpticalModel(b)
    path = root/'data/generated/trace_population_50000.csv'
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    pop = load_population(path)
    base_epoch = '2026-11-05T00:00:00Z'
    if not np.all(pop['epoch_utc']==base_epoch) or not np.all(pop['frame']=='TEME'):
        raise ValueError('Snapshot requires the nominal common epoch and frame')
    # Verify the elements reproduce the saved state before propagating them.
    zero = propagate_population(pop,0.)
    for field in ('x_km','y_km','z_km','vx_km_s','vy_km_s','vz_km_s'):
        np.testing.assert_allclose(zero[field],pop[field],rtol=1e-10,atol=1e-8)
    base_time = datetime.fromisoformat(base_epoch.replace('Z','+00:00'))
    period = 2*np.pi/case.frame_rate_rad_s
    scan = []
    best_count, best_elapsed = -1, 0.
    for elapsed in np.arange(0.,period,15.):
        epoch = (base_time+timedelta(seconds=float(elapsed))).isoformat().replace('+00:00','Z')
        state = propagate_population(pop,elapsed)
        geometry = classify_snapshot(state,model,case,approximate_sun_direction(epoch),
                                     elapsed_s=elapsed,geometry_only=True)
        visible_count = int(geometry['visible'].sum())
        scan.append([float(elapsed),epoch,int(geometry['in_fov'].sum()),visible_count])
        if visible_count>best_count:
            best_count,best_elapsed = visible_count,float(elapsed)
    epoch = (base_time+timedelta(seconds=best_elapsed)).isoformat().replace('+00:00','Z')
    sun = approximate_sun_direction(epoch)
    state = propagate_population(pop,best_elapsed)
    snapshot = classify_snapshot(state,model,case,sun,elapsed_s=best_elapsed)
    observer = np.array(snapshot['observer_position_km'])
    ranges = snapshot['range_km']
    sizes = pop['diameter_m']*100
    theta = b['PSF_FWHM']*model.derived(case)[1]
    unresolved = snapshot['unresolved']
    with (source/'snapshot_epoch_scan_450km.csv').open('w',newline='') as f:
        writer=csv.writer(f,lineterminator='\n')
        writer.writerow(['elapsed_s','epoch_utc','in_fov_objects','visible_objects'])
        writer.writerows(scan)
    detected = snapshot['detectable']
    count = int(detected.sum())
    visible_only = snapshot['visible'] & ~detected
    grey = ~snapshot['visible']
    publication_style()
    fig, ax = plt.subplots(figsize=(9,6), layout='constrained')
    x = np.geomspace(ranges.min()*.8, ranges.max()*1.1, 500)
    boundary = x*1e5*theta
    bottom = sizes.min()*.7
    ax.fill_between(x, bottom, np.maximum(bottom,boundary), color='red', alpha=.12,
                    label='Dominio de fuente no resuelta', zorder=0)
    ax.scatter(ranges[grey],sizes[grey],s=2,color='#737373',alpha=.4,linewidths=0,
               label=f'Resto de objetos: {int(grey.sum()):,}'.replace(',','.'),zorder=2)
    ax.scatter(ranges[visible_only],sizes[visible_only],s=24,color='#B57EDC',alpha=1,linewidths=.3,
               edgecolors='#553366',label=f'Visibles no detectables: {int(visible_only.sum())}',zorder=4)
    ax.scatter(ranges[detected],sizes[detected],s=22,color='#009E3C',alpha=1,linewidths=.3,
               edgecolors='black',label=f'Visibles y detectables: {count}',zorder=4)
    ax.plot(x,boundary,'--',color='red',lw=1.4,
            label=r'Límite: $d=r\,\mathrm{FWHM}_{\mathrm{px}}\,\delta$',zorder=3)
    ax.set(xscale='log',yscale='log',xlim=(x[0],x[-1]),
           ylim=(bottom,max(boundary.max(),sizes.max())*1.25),
           xlabel='Distancia al instrumento [km]',ylabel='Diámetro equivalente del objeto [cm]',
           title='TRACE — límite de fuente no resuelta · población nominal')
    ax.grid(which='major',lw=.5,alpha=.4);ax.grid(which='minor',lw=.3,alpha=.25)
    ax.text(.98,.96,'Debajo: fuente NO resuelta\nEncima: fuente resuelta',transform=ax.transAxes,
            ha='right',va='top',fontsize=10,bbox={'facecolor':'white','alpha':.8,'edgecolor':'none'})
    ax.legend(fontsize=9,loc='upper left',markerscale=2)
    fig.supxlabel(f'FOV={case.fov_deg:g}°, FWHM={b["PSF_FWHM"]:g} px; límite angular={theta:.6g} rad ({theta*ARCSEC_PER_RAD:.2f} arcsec).\n'
                  f'Observador a 450 km; época seleccionada: {epoch}.\n'
                  f'Instantánea ilustrativa: {int(snapshot["in_fov"].sum())} en FoV; {int(snapshot["visible"].sum())} visibles; {count} detectables (SNR ≥ 5).\n'
                  'Zenit, órbita ecuatorial prógrada; Sol aproximado y sombra terrestre cilíndrica. Máximo de visibles en una órbita muestreada cada 15 s; no es un conteo acumulado.',fontsize=9)
    name='trace_nominal_unresolved_source_limit_observer_450km'
    save_figure(fig,root/'outputs/optical/summary',name)
    with (source/'nominal_object_ranges_450km.csv').open('w',newline='') as f:
        columns=['range_km','unresolved','in_fov','earth_clear','sunlit','sun_safe','visible','detectable',
                 'phase_deg','angular_rate_rad_s','exposure_overlap_s','snr','unsaturated','partial_transit']
        w=csv.writer(f,lineterminator='\n');w.writerow(['object_id','diameter_cm']+columns)
        w.writerows(zip(pop['object_id'],sizes,*(snapshot[k] for k in columns)))
    audit={'population_sha256':digest,'objects':len(sizes),'unresolved_objects':int(unresolved.sum()),
           'resolved_objects':int((~unresolved).sum()),'observer_teme_km':observer.tolist(),
           'epoch_utc':epoch,'nominal_epoch_utc':base_epoch,
           'elapsed_s':best_elapsed,
           'epoch_selection':{'rule':'maximum visible count; earliest in a tie; no SNR selection',
                              'scan_step_s':15.,'scan_duration_s':float(period),'sampled_epochs':len(scan)},
           'propagation':'two body, fixed TEME axes of nominal epoch; no J2/drag/precession',
           'visible_not_detectable_objects':int(visible_only.sum()),'fov_deg':case.fov_deg,'fwhm_px':b['PSF_FWHM'],
           'pixel_scale_rad_px':model.derived(case)[1],'fwhm_angular_rad':theta,
           'fwhm_angular_arcsec':theta*ARCSEC_PER_RAD,'boundary_cm_per_km':theta*1e5,
           'visibility_classification_applied':True,'population_filtered':False,
           'in_fov_objects':int(snapshot['in_fov'].sum()),'visible_objects':int(snapshot['visible'].sum()),
           'visible_detectable_objects':count,'grey_objects':int(grey.sum()),
           'sun_direction_approximate_teme':sun.tolist(),
           'boresight_sun_deg':snapshot['boresight_sun_deg'],
           'observer_velocity_km_s':snapshot['observer_velocity_km_s'],
           'geometry_assumptions':[
               'Illustrative circular equatorial prograde observer; zenith radial, horizontal along-track, vertical orbit normal',
               'Rectangular field set by detector dimensions and nominal focal length',
               'Exposure centred at selected epoch; linear tangent-plane motion and field clipping',
               'Phases and apparent rates calculated per object; geometric albedo remains nominal',
               'Sun at infinity, low-precision mean-of-date direction approximated as TEME; no nutation correction',
               'Opaque spherical Earth; cylindrical shadow without penumbra; no spacecraft self-shadow',
               'Visible: inside field at exposure midpoint, Earth clear, illuminated, boresight solar exclusion',
               'Detectable: visible AND SNR>=5 AND unsaturated AND unresolved AND target solar exclusion',
               'Selected snapshot after short two-body propagation; no accumulated mission counts'],
           'png':name+'.png'}
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
    (source/'unresolved_population_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
