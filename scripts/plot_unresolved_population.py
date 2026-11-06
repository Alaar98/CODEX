"""Angular-size diagnostic and illustrative snapshot visibility of every nominal object."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from space_debris_detection.optical_validation import OpticalModel, StudyCase, load_baseline, ARCSEC_PER_RAD
from space_debris_detection.plotting import publication_style, save_figure, plt
from space_debris_detection.sensitivity import load_population
from space_debris_detection.snapshot import approximate_sun_direction, classify_snapshot


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
    observer = np.array([6371+case.observer_altitude_km, 0., 0.])
    positions = np.column_stack([pop[k] for k in ('x_km','y_km','z_km')])
    ranges = np.linalg.norm(positions-observer, axis=1)
    sizes = pop['diameter_m']*100
    theta = b['PSF_FWHM']*model.derived(case)[1]
    unresolved = sizes <= ranges*1e5*theta
    epoch = '2026-11-05T00:00:00Z'
    if not np.all(pop['epoch_utc']==epoch) or not np.all(pop['frame']=='TEME'):
        raise ValueError('Snapshot requires the nominal common epoch and frame')
    sun = approximate_sun_direction(epoch)
    snapshot = classify_snapshot(pop,model,case,sun)
    detected = snapshot['detectable']
    count = int(detected.sum())
    publication_style()
    fig, ax = plt.subplots(figsize=(9,6), layout='constrained')
    x = np.geomspace(ranges.min()*.8, ranges.max()*1.1, 500)
    boundary = x*1e5*theta
    bottom = sizes.min()*.7
    ax.fill_between(x, bottom, np.maximum(bottom,boundary), color='red', alpha=.12,
                    label='Dominio de fuente no resuelta', zorder=0)
    ax.scatter(ranges[~detected],sizes[~detected],s=2,color='#737373',alpha=.4,linewidths=0,
               label=f'Resto de objetos: {int((~detected).sum()):,}'.replace(',','.'),zorder=2)
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
                  'Observador TEME=(6821, 0, 0) km, altitud 450 km; época 2026-11-05T00:00:00Z.\n'
                  f'Instantánea ilustrativa: {int(snapshot["in_fov"].sum())} en FoV; {int(snapshot["visible"].sum())} visibles; {count} detectables (SNR ≥ 5).\n'
                  'Zenit, órbita ecuatorial prógrada; Sol aproximado y sombra terrestre cilíndrica. No es un conteo acumulado de misión.',fontsize=9)
    name='trace_nominal_unresolved_source_limit_observer_450km'
    save_figure(fig,root/'outputs/optical/summary',name)
    with (source/'nominal_object_ranges_450km.csv').open('w',newline='') as f:
        columns=['range_km','unresolved','in_fov','earth_clear','sunlit','sun_safe','visible','detectable',
                 'phase_deg','angular_rate_rad_s','exposure_overlap_s','snr','unsaturated','partial_transit']
        w=csv.writer(f,lineterminator='\n');w.writerow(['object_id','diameter_cm']+columns)
        w.writerows(zip(pop['object_id'],sizes,*(snapshot[k] for k in columns)))
    audit={'population_sha256':digest,'objects':len(sizes),'unresolved_objects':int(unresolved.sum()),
           'resolved_objects':int((~unresolved).sum()),'observer_teme_km':observer.tolist(),
           'epoch_utc':'2026-11-05T00:00:00Z','fov_deg':case.fov_deg,'fwhm_px':b['PSF_FWHM'],
           'pixel_scale_rad_px':model.derived(case)[1],'fwhm_angular_rad':theta,
           'fwhm_angular_arcsec':theta*ARCSEC_PER_RAD,'boundary_cm_per_km':theta*1e5,
           'visibility_classification_applied':True,'population_filtered':False,
           'in_fov_objects':int(snapshot['in_fov'].sum()),'visible_objects':int(snapshot['visible'].sum()),
           'visible_detectable_objects':count,'grey_objects':int((~detected).sum()),
           'sun_direction_approximate_teme':sun.tolist(),
           'boresight_sun_deg':snapshot['boresight_sun_deg'],
           'observer_velocity_km_s':snapshot['observer_velocity_km_s'],
           'geometry_assumptions':[
               'Illustrative circular equatorial prograde observer; zenith +X, horizontal +Y, vertical +Z',
               'Rectangular field set by detector dimensions and nominal focal length',
               'Exposure centred at nominal epoch; linear tangent-plane motion and field clipping',
               'Phases and apparent rates calculated per object; geometric albedo remains nominal',
               'Sun at infinity, low-precision mean-of-date direction approximated as TEME; no nutation correction',
               'Opaque spherical Earth; cylindrical shadow without penumbra; no spacecraft self-shadow',
               'Visible: inside field at exposure midpoint, Earth clear, illuminated, boresight solar exclusion',
               'Detectable: visible AND SNR>=5 AND unsaturated AND unresolved AND target solar exclusion',
               'Single snapshot only; no orbit propagation or accumulated mission counts'],
           'png':name+'.png'}
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
    (source/'unresolved_population_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
