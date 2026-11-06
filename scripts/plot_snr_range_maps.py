"""Nominal instrument SNR maps: apparent magnitude and transverse velocity."""
import csv
from dataclasses import asdict
import json
from pathlib import Path

import numpy as np

from space_debris_detection.optical_validation import OpticalModel, StudyCase, load_baseline
from space_debris_detection.plotting import publication_style, save_figure, plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


def limiting_magnitude(model, case, ranges_m):
    """Solve S^2 = threshold^2 * (S + background/read variance)."""
    zero=model.evaluate(case,ranges_m,magnitude_ab=0.)
    b=model.b;threshold=b['SNR_min']
    noise=zero['pixels']*((zero['background_e_per_pixel_s']+b['I_dark'])*b['t_int']+b['sigma_read']**2)
    required=(threshold**2+np.sqrt(threshold**4+4*threshold**2*noise))/2
    return -2.5*np.log10(required/zero['signal_e'])


def main():
    root=Path(__file__).resolve().parents[1]
    source=root/'data/generated/optical';output=root/'outputs/optical/summary'
    manifest=json.loads((source/'manifest.json').read_text())
    b=load_baseline(root/'docs/references'/manifest['workbook'])
    if b.source_sha256!=manifest['workbook_sha256']:raise ValueError('Stale baseline: regenerate optical study')
    nominal=StudyCase(**manifest['nominal_instrument_case'])
    if nominal.observer_altitude_km!=450:raise ValueError('Expected nominal 450 km observer')
    model=OpticalModel(b);diameter=.05
    publication_style()
    ranges_mag=np.geomspace(10.,2e7,1001)
    magnitudes=np.linspace(0,20,601)
    mag_result=model.evaluate(nominal,ranges_mag[None,:],magnitude_ab=magnitudes[:,None])
    mag_limit=limiting_magnitude(model,nominal,ranges_mag)
    # Independent substitution back into the radiometric model verifies the curve.
    assert np.allclose(model.evaluate(nominal,ranges_mag,magnitude_ab=mag_limit)['snr'],b['SNR_min'],rtol=1e-12)
    speed_ranges=np.geomspace(10.,2e6,1401)
    velocities=np.linspace(0.,15.,751)
    # StudyCase keeps the nominal scalar speed; override the actual camera rate
    # at each grid point, using the existing positive along-track LVLH model.
    omega=np.abs(velocities[:,None]*1000/speed_ranges[None,:]-nominal.frame_rate_rad_s)
    speed_result=model.evaluate(nominal,speed_ranges[None,:],diameter_m=diameter,apparent_rate_rad_s=omega)
    handles=[Line2D([0],[0],color='red',linestyle='--',lw=1.5,label='SNR = 5'),
             Patch(facecolor='red',alpha=.12,label='SNR < 5'),
             Patch(facecolor='none',edgecolor='#777777',hatch='////',label='Saturación: fuera del modelo lineal')]
    def decorate(ax,fig,name,caption):
        ax.set_xscale('log');ax.set_xlabel('Distancia entre observador y objeto [km]')
        ax.set_axisbelow(True);ax.grid(which='major',lw=.5,alpha=.4);ax.grid(which='minor',lw=.3,alpha=.25)
        ax.legend(handles=handles,loc='upper left',fontsize=9)
        fig.supxlabel(caption,fontsize=9)
        save_figure(fig,output,name)
    caption=(f'D=80 mm, FOV=14°, exposición=77 ms, High Gain; observador circular a 450 km, instrumento fijo al zenit.\n'
             'Se admiten tránsitos parciales; fondo integrado durante toda la exposición. Resultados condicionales del instrumento.')
    fig,ax=plt.subplots(figsize=(9,6),layout='constrained')
    x=ranges_mag/1000
    ax.fill_between(x,mag_limit,magnitudes[-1],color='red',alpha=.12,zorder=0)
    ax.contourf(x,magnitudes,(~mag_result['unsaturated']).astype(float),levels=[.5,1.5],
                colors='none',hatches=['////'],alpha=.4)
    ax.plot(x,mag_limit,color='red',ls='--',lw=1.5)
    ax.set(xlim=(x[0],x[-1]),ylim=(magnitudes[0],magnitudes[-1]),
           ylabel='Magnitud aparente AB [mag]',title='TRACE — magnitud aparente frente a distancia')
    decorate(ax,fig,'trace_instrument_reference_apparent_magnitude_vs_range_snr5_450km',
             caption+'\n'+r'$v_\perp=5$ km/s. Magnitud AB equivalente en 450–750 nm; un valor mayor indica una fuente más débil.')
    fig,ax=plt.subplots(figsize=(9,6),layout='constrained')
    x=speed_ranges/1000
    ax.contourf(x,velocities,(speed_result['snr']<b['SNR_min']).astype(float),levels=[.5,1.5],
                colors=['red'],alpha=.12)
    ax.contourf(x,velocities,(~speed_result['unsaturated']).astype(float),levels=[.5,1.5],
                colors='none',hatches=['////'],alpha=.4)
    unresolved_boundary=diameter/(b['PSF_FWHM']*model.derived(nominal)[1])/1000
    ax.axvspan(x[0],unresolved_boundary,color='#B0B0B0',alpha=.2)
    contour=ax.contour(x,velocities,speed_result['snr'],levels=[b['SNR_min']],
                       colors=['red'],linestyles=['--'],linewidths=1.5)
    ax.set(xlim=(x[0],x[-1]),ylim=(velocities[0],velocities[-1]),
           ylabel=r'Velocidad relativa transversal $v_\perp$ [km/s]',
           title='TRACE — velocidad transversal frente a distancia · objeto de 5 cm')
    handles.append(Patch(facecolor='#B0B0B0',alpha=.2,label='Fuente resuelta: fuera del modelo puntual'))
    decorate(ax,fig,'trace_instrument_reference_transverse_velocity_vs_range_5cm_snr5_450km',
             caption+'\nDiámetro=5 cm, albedo geométrico=0,2, fase=60°. Velocidad transversal relativa en sentido along-track.')
    # Audit contour vertices against the original evaluator, accounting for
    # interpolation and discontinuous integer extraction-pixel boundaries.
    vertex_errors=[]
    with (source/'snr5_velocity_range_5cm_boundary.csv').open('w',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['segment','range_km','transverse_velocity_km_s','snr_evaluated'])
        for j,segment in enumerate(contour.allsegs[0]):
            if not len(segment):continue
            rate=np.abs(segment[:,1]*1000/(segment[:,0]*1000)-nominal.frame_rate_rad_s)
            result=model.evaluate(nominal,segment[:,0]*1000,diameter_m=diameter,apparent_rate_rad_s=rate)
            w.writerows(zip(np.full(len(segment),j),segment[:,0],segment[:,1],result['snr']))
            vertex_errors.extend(np.abs(result['snr']-b['SNR_min']).tolist())
    with (source/'snr5_magnitude_range_boundary.csv').open('w',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['range_km','limiting_apparent_magnitude_ab'])
        w.writerows(zip(ranges_mag/1000,mag_limit))
    np.savez_compressed(source/'snr_range_maps_450km.npz',range_magnitude_m=ranges_mag,
                        magnitudes_ab=magnitudes,snr_magnitude=mag_result['snr'],
                        unsaturated_magnitude=mag_result['unsaturated'],range_velocity_m=speed_ranges,
                        velocities_km_s=velocities,snr_velocity=speed_result['snr'],
                        unsaturated_velocity=speed_result['unsaturated'],unresolved_velocity=speed_result['unresolved'])
    reference=model.range_intervals(nominal,diameter,np.geomspace(1,2e7,2049))
    audit={'instrument_case':asdict(nominal),'workbook':manifest['workbook'],'workbook_sha256':b.source_sha256,
           'detector_baseline_si':b.values,'velocity_plot_diameter_m':diameter,'snr_threshold':b['SNR_min'],
           'magnitude_system':'equivalent band AB over 450–750 nm; flat-Fnu calibration',
           'apparent_magnitude_grid':[float(magnitudes[0]),float(magnitudes[-1]),len(magnitudes)],
           'magnitude_range_grid_m':[float(ranges_mag[0]),float(ranges_mag[-1]),len(ranges_mag)],
           'velocity_grid_km_s':[float(velocities[0]),float(velocities[-1]),len(velocities)],
           'velocity_range_grid_m':[float(speed_ranges[0]),float(speed_ranges[-1]),len(speed_ranges)],
           'red_shading':'SNR<5 only; not the complement of complete detectability',
           'grey_shading':'resolved source (velocity plot only); point-source SNR extrapolated outside domain',
           'grey_hatching':'saturation; formal linear-model SNR is not a valid performance prediction there',
           'angular_motion':'abs(v_perp/r-n_LVLH), positive along-track zenith simplification',
           'partial_transits':'maximum overlap central crossing; background and dark integrate full exposure',
           'magnitude_distance_convention':'apparent magnitude already fixes received flux; range affects motion only, no second inverse-square loss',
           'source_size_in_magnitude_plot':'not specified; point-source assumption, unresolved size not inferred from magnitude',
           'phase_albedo_in_magnitude_plot':'already encoded by apparent flux; not multiplied into AB brightness again',
           'range_scan_limitation':'instrument envelope; not a set of available LEO encounter distances',
           'population_used':False,'mission_detection_counts_computed':False,
           'velocity_contour_max_abs_snr_error':max(vertex_errors,default=None),
           'velocity_contour_method':'linear interpolation of sampled SNR; integer extraction pixels can produce jumps',
           'nominal_5cm_intervals_m':reference,
           'figures':['trace_instrument_reference_apparent_magnitude_vs_range_snr5_450km.png',
                      'trace_instrument_reference_transverse_velocity_vs_range_5cm_snr5_450km.png']}
    (source/'snr_range_maps_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps({'figures':audit['figures'],'5cm_intervals':reference,
                      'maximum_contour_snr_error':audit['velocity_contour_max_abs_snr_error']},indent=2))


if __name__=='__main__':main()
