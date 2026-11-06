"""Short sampled comparison of equatorial and SSO observer geometries."""
import csv
from dataclasses import asdict
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path

import numpy as np
from space_debris_detection.optical_validation import OpticalModel, StudyCase, load_baseline
from space_debris_detection.plotting import publication_style, save_figure, plt
from space_debris_detection.sensitivity import load_population
from space_debris_detection.snapshot import approximate_sun_direction, classify_snapshot, propagate_population


def sso_inclination_deg(altitude_km):
    # First-order secular J2 nodal rate, circular orbit, tropical year.
    mu,J2,R=398600.4418,1.08262668e-3,6378.137
    a=6371+altitude_km
    n=np.sqrt(mu/a**3)
    solar_rate=2*np.pi/(365.2422*86400)
    return float(np.degrees(np.arccos(-solar_rate/(1.5*J2*n*(R/a)**2))))


def main():
    root=Path(__file__).resolve().parents[1]
    source=root/'data/generated/optical';output=root/'outputs/optical/summary'
    manifest=json.loads((source/'manifest.json').read_text())
    case=StudyCase(**manifest['nominal_instrument_case'])
    b=load_baseline(root/'docs/references'/manifest['workbook']);model=OpticalModel(b)
    path=root/'data/generated/trace_population_50000.csv'
    sha=hashlib.sha256(path.read_bytes()).hexdigest();pop=load_population(path)
    epoch0='2026-11-05T00:00:00Z';base=datetime.fromisoformat(epoch0.replace('Z','+00:00'))
    sun0=approximate_sun_direction(epoch0)
    sun_ra=np.degrees(np.arctan2(sun0[1],sun0[0]))%360
    inc=sso_inclination_deg(case.observer_altitude_km)
    scenarios=[{'id':'equatorial','label':'Ecuatorial','inclination_deg':0.,'raan_deg':0.,'ltan_h':None}]
    for ltan in (6.,10.5,13.5,18.):
        scenarios.append({'id':f'sso_ltan_{ltan:g}'.replace('.','p'),
                          'label':f'SSO LTAN {int(ltan):02d}:{int((ltan%1)*60):02d}',
                          'inclination_deg':inc,'raan_deg':float((sun_ra+15*(ltan-12))%360),'ltan_h':ltan})
    times=np.arange(0.,2*np.pi/case.frame_rate_rad_s,15.)
    records=[];samples={s['id']:[] for s in scenarios}
    unique={s['id']:set() for s in scenarios};unique_visible={s['id']:set() for s in scenarios}
    for elapsed in times:
        epoch=(base+timedelta(seconds=float(elapsed))).isoformat().replace('+00:00','Z')
        state=propagate_population(pop,elapsed);sun=approximate_sun_direction(epoch)
        for scenario in scenarios:
            kwargs={'elapsed_s':elapsed,'observer_inclination_deg':scenario['inclination_deg'],
                    'observer_raan_deg':scenario['raan_deg']}
            geo=classify_snapshot(state,model,case,sun,geometry_only=True,**kwargs)
            selected=geo['visible'];idx=np.flatnonzero(selected)
            unique_visible[scenario['id']].update(idx.tolist())
            nd=0;max_snr=0.
            if len(idx):
                subset={k:v[selected] for k,v in state.items()}
                result=classify_snapshot(subset,model,case,sun,**kwargs)
                ids=idx[result['detectable']]
                unique[scenario['id']].update(ids.tolist());nd=len(ids)
                max_snr=float(np.max(result['snr']))
            row={'scenario':scenario['id'],'elapsed_s':float(elapsed),'epoch_utc':epoch,
                 'in_fov':int(geo['in_fov'].sum()),'visible':len(idx),'detectable':nd,'visible_max_snr':max_snr}
            records.append(row);samples[scenario['id']].append(row)
    summary=[]
    for scenario in scenarios:
        rows=samples[scenario['id']];best=max(rows,key=lambda r:r['visible'])
        summary.append({**scenario,'semi_major_axis_km':6371+case.observer_altitude_km,'eccentricity':0.,
                        'initial_u_deg':0.,'peak_visible':best['visible'],
                        'epoch_peak_visible':best['epoch_utc'],'elapsed_peak_visible_s':best['elapsed_s'],
                        'detectable_at_peak_visible':best['detectable'],
                        'peak_detectable':max(r['detectable'] for r in rows),
                        'mean_visible_per_sample':float(np.mean([r['visible'] for r in rows])),
                        'mean_detectable_per_sample':float(np.mean([r['detectable'] for r in rows])),
                        'unique_sampled_visible_objects':len(unique_visible[scenario['id']]),
                        'unique_sampled_detectable_objects':len(unique[scenario['id']]),
                        'maximum_visible_snr':max(r['visible_max_snr'] for r in rows)})
    for name,rows in [('sso_observer_scan.csv',records),('sso_observer_comparison.csv',summary)]:
        with (source/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    publication_style()
    fig,axes=plt.subplots(2,1,figsize=(10,7),sharex=True,layout='constrained')
    for scenario in scenarios:
        rows=samples[scenario['id']]
        for ax,key in zip(axes,('visible','detectable')):
            ax.plot(times/60,[r[key] for r in rows],lw=1,label=scenario['label'])
    axes[0].set(ylabel='Objetos visibles',title='TRACE — observador ecuatorial y SSO a 450 km')
    axes[1].set(xlabel='Tiempo desde 2026-11-05 00:00 UTC [min]',ylabel='Objetos detectables (SNR ≥ 5)')
    for ax in axes:ax.grid(which='both',lw=.4,alpha=.3)
    axes[0].legend(ncol=3,fontsize=8)
    fig.supxlabel('Misma población, instrumento y muestreo de 15 s. Propagación breve de dos cuerpos; inclinación SSO calculada con J2.\n'
                  'Conteos simultáneos en las muestras, no eventos completos ni detecciones acumuladas continuas.',fontsize=9)
    save_figure(fig,output,'trace_nominal_equatorial_vs_sso_450km_sampled_counts')
    # Select the SSO with most unique sampled detections; illustrate its sample
    # with most simultaneous detections, then most visible, earliest in a tie.
    best=max(summary[1:],key=lambda r:r['unique_sampled_detectable_objects'])
    selected=max(samples[best['id']],key=lambda r:(r['detectable'],r['visible']))
    elapsed=selected['elapsed_s']
    state=propagate_population(pop,elapsed)
    result=classify_snapshot(state,model,case,approximate_sun_direction(selected['epoch_utc']),
                             elapsed_s=elapsed,observer_inclination_deg=inc,observer_raan_deg=best['raan_deg'])
    ranges=result['range_km'];sizes=pop['diameter_m']*100;theta=b['PSF_FWHM']*model.derived(case)[1]
    fig,ax=plt.subplots(figsize=(9,6),layout='constrained')
    x=np.geomspace(ranges.min()*.8,ranges.max()*1.1,500);bottom=sizes.min()*.7;line=x*1e5*theta
    top=max(line.max(),sizes.max())*1.25
    ax.fill_between(x,line,top,color='red',alpha=.12,label='Fuentes resueltas: fuera del modelo puntual',zorder=0)
    masks=[~result['visible'],result['visible']&~result['detectable'],result['detectable']]
    for mask,color,label,sz in zip(masks,('#737373','#B57EDC','#009E3C'),
                                  ('Resto','Visibles no detectables','Visibles y detectables'),(2,24,24)):
        ax.scatter(ranges[mask],sizes[mask],s=sz,color=color,alpha=.4 if sz==2 else 1,
                   linewidths=0,label=f'{label}: {int(mask.sum())}',zorder=2 if sz==2 else 4)
    ax.plot(x,line,'r--',lw=1.3,label=r'Límite $d=r\,\mathrm{FWHM}_{\mathrm{px}}\delta$')
    ax.set(xscale='log',yscale='log',xlim=(x[0],x[-1]),ylim=(bottom,top),
           xlabel='Distancia al instrumento [km]',ylabel='Diámetro equivalente [cm]',
           title=f'TRACE — SSO a 450 km · {best["label"]}')
    ax.legend(fontsize=9);ax.grid(which='both',lw=.3,alpha=.3)
    fig.supxlabel(f'i={inc:.4f}°, RAAN={best["raan_deg"]:.4f}°; época {selected["epoch_utc"]}. FOV=14°, apertura=80 mm.\n'
                  'Caso con más objetos distintos detectables muestreados; imagen con máximo de detecciones y después visibles.\nDebajo de la línea: fuente no resuelta. Instantánea seleccionada, no rendimiento medio.',fontsize=9)
    png='trace_nominal_unresolved_source_limit_sso_observer_450km'
    save_figure(fig,output,png)
    with (source/'sso_selected_snapshot_objects.csv').open('w',newline='') as f:
        fields=['range_km','visible','detectable','in_fov','sunlit','snr','phase_deg','unresolved']
        w=csv.writer(f,lineterminator='\n');w.writerow(['object_id','diameter_cm']+fields)
        w.writerows(zip(pop['object_id'],sizes,*(result[k] for k in fields)))
    audit={'population_sha256':sha,'baseline_sha256':b.source_sha256,'instrument':asdict(case),
           'epoch0':epoch0,'duration_s':float(2*np.pi/case.frame_rate_rad_s),'step_s':15.,'samples_per_orbit':len(times),
           'sso_inclination_deg':inc,'J2':1.08262668e-3,'J2_reference_radius_km':6378.137,
           'solar_rate_rad_s':2*np.pi/(365.2422*86400),'initial_sun_ra_deg':float(sun_ra),
           'ltan_convention':'approximate mean solar LTAN; RAAN=solar_RA+15*(LTAN-12)',
           'short_propagation':'two body for all objects and observer; fixed nominal TEME axes, J2 used only to choose SSO inclination',
           'limitations':['15 s gaps miss short passes; unique sampled objects are not complete encounter counts',
                          'one orbit and one initial phase do not establish mission improvement',
                          'Sun and cylindrical shadow approximate; fixed sky background and nominal albedo'],
           'scenarios':summary,'selected_sso_scenario':best,'selected_sso_snapshot':selected,
           'snapshot_selection':'scenario with most unique sampled detections; sample max simultaneous detectable, then visible, earliest tie','selected_snapshot_png':png+'.png'}
    assert hashlib.sha256(path.read_bytes()).hexdigest()==sha
    (source/'sso_observer_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
