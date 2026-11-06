"""All nominal objects in magnitude/range and transverse-speed/range plots."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from space_debris_detection.optical_validation import OpticalModel,StudyCase,load_baseline
from space_debris_detection.plotting import publication_style,save_figure,plt
from space_debris_detection.sensitivity import load_population
from space_debris_detection.snapshot import propagate_population,approximate_sun_direction,classify_snapshot
from scripts.plot_snr_range_maps import limiting_magnitude
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


def size_groups(diameter_m):
    cm=np.asarray(diameter_m)*100
    if np.any(cm<1):raise ValueError('Nominal population requires diameter >= 1 cm')
    return np.select([cm<5,cm<10],[0,1],default=2)


def main():
    root=Path(__file__).resolve().parents[1];source=root/'data/generated/optical'
    output=root/'outputs/optical/summary'
    audit0=json.loads((source/'sso_observer_audit.json').read_text())
    case=StudyCase(**audit0['instrument'])
    manifest=json.loads((source/'manifest.json').read_text())
    b=load_baseline(root/'docs/references'/manifest['workbook'])
    if b.source_sha256!=audit0['baseline_sha256']:raise ValueError('Stale SSO baseline')
    model=OpticalModel(b)
    path=root/'data/generated/trace_population_50000.csv';sha=hashlib.sha256(path.read_bytes()).hexdigest()
    if sha!=audit0['population_sha256']:raise ValueError('Stale SSO population')
    pop=load_population(path);selected=audit0['selected_sso_snapshot'];scenario=audit0['selected_sso_scenario']
    state=propagate_population(pop,selected['elapsed_s'])
    snapshot=classify_snapshot(state,model,case,approximate_sun_direction(selected['epoch_utc']),
        elapsed_s=selected['elapsed_s'],observer_inclination_deg=scenario['inclination_deg'],
        observer_raan_deg=scenario['raan_deg'],observer_initial_u_deg=scenario['initial_u_deg'])
    ranges=snapshot['range_km'];detected=snapshot['detectable'];visible=snapshot['visible']
    # Physical transverse relative speed, before subtracting camera rotation.
    positions=np.column_stack([state[k] for k in ('x_km','y_km','z_km')])
    velocities=np.column_stack([state[k] for k in ('vx_km_s','vy_km_s','vz_km_s')])
    los=(positions-np.array(snapshot['observer_position_km']))/ranges[:,None]
    vrel=velocities-np.array(snapshot['observer_velocity_km_s'])
    transverse=np.linalg.norm(vrel-los*np.sum(vrel*los,axis=1)[:,None],axis=1)
    photometry=model.evaluate(case,ranges*1000,diameter_m=pop['diameter_m'],
        phase_deg=snapshot['phase_deg'],apparent_rate_rad_s=snapshot['angular_rate_rad_s'],
        exposure_overlap_s=snapshot['exposure_overlap_s'])
    # A shadowed object has no direct reflected solar flux in this model.
    direct_flux=snapshot['sunlit'] & snapshot['earth_clear']
    magnitude=np.where(direct_flux,photometry['magnitude_ab'],np.nan)
    groups=size_groups(pop['diameter_m'])
    colors=('#0072B2','#009E73','#B57EDC')
    labels=(r'$1\leq d<5$ cm',r'$5\leq d<10$ cm',r'$d\geq10$ cm')
    assert len(ranges)==50000 and int(detected.sum())==selected['detectable']
    assert all(np.isfinite(v).all() for v in (ranges,transverse))
    xmin,xmax=float(ranges.min()*.8),float(ranges.max()*1.1)
    finite=magnitude[np.isfinite(magnitude)]
    low=float(np.floor(min(finite.min(),8.))-1)
    high=float(np.ceil(max(finite.max(),14.))+1)
    shadow_y=high+2
    plot_magnitude=np.where(np.isfinite(magnitude),magnitude,shadow_y)
    publication_style()
    handles=[Line2D([0],[0],marker='o',ls='none',color=color,label=label,ms=5)
             for color,label in zip(colors,labels)]
    handles += [Line2D([0],[0],marker='x',color='#333333',ls='none',label=f'No detectables ({int((~detected).sum()):,})'.replace(',','.'),ms=5),
                Line2D([0],[0],marker='*',markerfacecolor='white',markeredgecolor='black',ls='none',
                       label=f'Detectables ({int(detected.sum())})',ms=10),
                Line2D([0],[0],color='red',ls='--',label='SNR = 5 de referencia'),
                Patch(facecolor='red',alpha=.1,label='SNR < 5 de referencia')]
    def points(ax,y):
        rendered=0
        for group,color in enumerate(colors):
            mask=(groups==group)&~detected
            ax.scatter(ranges[mask],y[mask],s=4,marker='x',color=color,alpha=.3,linewidths=.35,zorder=3)
            yes=(groups==group)&detected
            ax.scatter(ranges[yes],y[yes],s=160,marker='*',facecolor=color,edgecolor='black',linewidths=.9,zorder=7)
            rendered+=int(mask.sum()+yes.sum())
        assert rendered==50000
    def finish(ax,fig,name,extra):
        ax.set(xscale='log',xlim=(xmin,xmax),xlabel='Distancia entre observador y objeto [km]')
        ax.grid(which='major',lw=.5,alpha=.4);ax.grid(which='minor',lw=.3,alpha=.25)
        fig.subplots_adjust(left=.10,right=.98,bottom=.21,top=.80)
        fig.legend(handles=handles,fontsize=8,loc='upper center',bbox_to_anchor=(.5,.995),ncol=3,frameon=False)
        fig.supxlabel(f'Población nominal: 50.000 objetos · SSO 450 km, LTAN 06:00 · {selected["epoch_utc"]}.\n'
            'D=80 mm, FOV=14°, exposición=77 ms, albedo=0,2. Detectabilidad calculada individualmente, incluida la visibilidad.\n'
            +extra,fontsize=8,y=.015)
        save_figure(fig,output,name)
    names=[]
    fig,ax=plt.subplots(figsize=(10,7),layout='none')
    x=np.geomspace(xmin,xmax,1001);limit=limiting_magnitude(model,case,x*1000)
    ax.fill_between(x,limit,high,color='red',alpha=.1,zorder=0)
    ax.plot(x,limit,'r--',lw=1.3,zorder=2)
    ax.axhspan(high+.8,shadow_y+.6,color='#EEEEEE',zorder=0)
    ax.axhline(high+.8,color='#777777',lw=.6,ls=':')
    points(ax,plot_magnitude)
    ax.set(ylim=(low,shadow_y+.6),ylabel='Magnitud aparente AB [mag]',
           title='TRACE — magnitud aparente frente a distancia · 50.000 objetos')
    ticks=list(ax.get_yticks());ticks=[v for v in ticks if low<=v<=high]+[shadow_y]
    ax.set_yticks(ticks,labels=[f'{v:g}' for v in ticks[:-1]]+['Sin señal'])
    # Shadow band is above the numerical magnitude axis, not a finite magnitude.
    ax.text(.99,.03,'«Sin señal»: sombra u ocultación terrestre; sin magnitud solar finita',transform=ax.transAxes,
            ha='right',fontsize=8,bbox={'facecolor':'white','alpha':.9,'edgecolor':'none'})
    name='trace_nominal_sso450km_apparent_magnitude_vs_range_all_objects';names.append(name+'.png')
    finish(ax,fig,name,'Referencia roja: v transversal=5 km/s. No es un umbral universal para objetos con velocidades distintas.')
    fig,ax=plt.subplots(figsize=(10,7),layout='none')
    y=np.linspace(0.,max(15.,float(transverse.max())*1.05),601);x=np.geomspace(xmin,xmax,1001)
    rate=np.abs(y[:,None]*1000/(x[None,:]*1000)-case.frame_rate_rad_s)
    reference=model.evaluate(case,x[None,:]*1000,diameter_m=.05,apparent_rate_rad_s=rate)
    ax.contourf(x,y,(reference['snr']<5).astype(float),levels=[.5,1.5],colors=['red'],alpha=.1,zorder=0)
    ax.contour(x,y,reference['snr'],levels=[5],colors=['red'],linestyles=['--'],linewidths=1.3,zorder=2)
    points(ax,transverse)
    ax.set(ylim=(0,y[-1]),ylabel=r'Velocidad relativa transversal $v_\perp$ [km/s]',
           title='TRACE — velocidad transversal frente a distancia · 50.000 objetos')
    name='trace_nominal_sso450km_transverse_velocity_vs_range_all_objects';names.append(name+'.png')
    finish(ax,fig,name,'Referencia roja: d=5 cm, fase=60°, movimiento along-track. Los puntos usan su tamaño, fase y movimiento propios.')
    with (source/'population_snr_scatter_objects.csv').open('w',newline='') as f:
        w=csv.writer(f,lineterminator='\n')
        w.writerow(['object_id','diameter_cm','size_group','range_km','apparent_magnitude_ab',
                    'magnitude_plot_y','sunlit','transverse_speed_km_s','angular_rate_rad_s','phase_deg',
                    'snr','visible','detectable','in_fov','earth_clear','unsaturated','unresolved'])
        for j in range(len(ranges)):
            w.writerow([pop['object_id'][j],pop['diameter_m'][j]*100,labels[groups[j]],ranges[j],
                float(magnitude[j]) if np.isfinite(magnitude[j]) else '',plot_magnitude[j],snapshot['sunlit'][j],
                transverse[j],snapshot['angular_rate_rad_s'][j],snapshot['phase_deg'][j],snapshot['snr'][j],
                visible[j],detected[j],snapshot['in_fov'][j],snapshot['earth_clear'][j],
                snapshot['unsaturated'][j],snapshot['unresolved'][j]])
    audit={'population_sha256':sha,'baseline_sha256':b.source_sha256,'epoch_utc':selected['epoch_utc'],
           'observer_scenario':scenario,'observer_position_km':snapshot['observer_position_km'],
           'observer_velocity_km_s':snapshot['observer_velocity_km_s'],'objects_in_each_figure':len(ranges),
           'size_groups':[{'label':label,'color':color,'count':int((groups==j).sum())}
                          for j,(label,color) in enumerate(zip(labels,colors))],
           'visible':int(visible.sum()),'detectable':int(detected.sum()),'not_detectable':int((~detected).sum()),
           'sunlit':int(snapshot['sunlit'].sum()),'direct_flux_objects':int(direct_flux.sum()),'no_direct_signal_band_objects':int((~direct_flux).sum()),
           'no_direct_signal_band_plot_y':shadow_y,'no_direct_signal_band_convention':'categorical display row, never a finite apparent magnitude',
           'magnitude_model':'AB-equivalent reflected solar flux; geometric phase per object, nominal albedo; shadowed or Earth-occulted magnitude undefined',
           'velocity_definition':'norm of relative inertial velocity projected perpendicular to observer-object LOS; excludes camera rotation',
           'snr_motion':'camera angular rate includes full vector LVLH rotation, per existing snapshot model',
           'markers':{'x':'not detectable','star_black_outline':'detectable'},
           'reference_curves':'nominal 5 km/s for magnitude; 5 cm / 60 deg / along-track for velocity; red shading not a classification of all points',
           'selection':'reuse previously selected SSO 06:00 sample, no new epoch optimisation',
           'figures':names}
    assert hashlib.sha256(path.read_bytes()).hexdigest()==sha
    (source/'population_snr_scatter_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
