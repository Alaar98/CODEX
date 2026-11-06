"""Angular-size diagnostic of every nominal object, without visibility filtering."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from space_debris_detection.optical_validation import OpticalModel, StudyCase, load_baseline, ARCSEC_PER_RAD
from space_debris_detection.plotting import publication_style, save_figure, plt
from space_debris_detection.sensitivity import load_population


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
    publication_style()
    fig, ax = plt.subplots(figsize=(9,6), layout='constrained')
    x = np.geomspace(ranges.min()*.8, ranges.max()*1.1, 500)
    boundary = x*1e5*theta
    bottom = sizes.min()*.7
    ax.fill_between(x, bottom, np.maximum(bottom,boundary), color='red', alpha=.12,
                    label='Dominio de fuente no resuelta', zorder=0)
    ax.scatter(ranges, sizes, s=2, color='#0072B2', alpha=.35, linewidths=0,
               label='50.000 objetos nominales', zorder=2)
    ax.plot(x,boundary,'--',color='red',lw=1.4,
            label=r'Límite: $d=r\,\mathrm{FWHM}_{\mathrm{px}}\,\delta$',zorder=3)
    ax.set(xscale='log',yscale='log',xlim=(x[0],x[-1]),
           ylim=(bottom,max(boundary.max(),sizes.max())*1.25),
           xlabel='Distancia al instrumento [km]',ylabel='Diámetro equivalente del objeto [cm]',
           title='TRACE — límite de fuente no resuelta · población nominal')
    ax.grid(which='major',lw=.5,alpha=.4);ax.grid(which='minor',lw=.3,alpha=.25)
    ax.legend(fontsize=9,loc='upper left')
    fig.supxlabel(f'FOV={case.fov_deg:g}°, FWHM={b["PSF_FWHM"]:g} px; límite angular={theta:.6g} rad ({theta*ARCSEC_PER_RAD:.2f} arcsec).\n'
                  'Observador TEME=(6821, 0, 0) km, altitud 450 km; época 2026-11-05T00:00:00Z.\n'
                  'Todos los objetos, incluidos los ocultos por la Tierra y fuera del campo. No es una gráfica de detecciones.',fontsize=9)
    name='trace_nominal_unresolved_source_limit_observer_450km'
    save_figure(fig,root/'outputs/optical/summary',name)
    with (source/'nominal_object_ranges_450km.csv').open('w',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['object_id','range_km','diameter_cm','unresolved'])
        w.writerows(zip(pop['object_id'],ranges,sizes,unresolved))
    audit={'population_sha256':digest,'objects':len(sizes),'unresolved_objects':int(unresolved.sum()),
           'resolved_objects':int((~unresolved).sum()),'observer_teme_km':observer.tolist(),
           'epoch_utc':'2026-11-05T00:00:00Z','fov_deg':case.fov_deg,'fwhm_px':b['PSF_FWHM'],
           'pixel_scale_rad_px':model.derived(case)[1],'fwhm_angular_rad':theta,
           'fwhm_angular_arcsec':theta*ARCSEC_PER_RAD,'boundary_cm_per_km':theta*1e5,
           'visibility_filter_applied':False,'png':name+'.png'}
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
    (source/'unresolved_population_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
