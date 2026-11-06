"""Compare exact target sizes and describe the unchanged nominal population."""

import csv
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path

import numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import AutoMinorLocator, LogLocator, MultipleLocator
from openpyxl import load_workbook
from openpyxl.worksheet.table import Table, TableStyleInfo

from space_debris_detection.optical_validation import OpticalModel, StudyCase, load_baseline
from space_debris_detection.plotting import publication_style, save_figure, plt
from space_debris_detection.sensitivity import load_population


def main():
    root=Path(__file__).resolve().parents[1]
    source=root/'data/generated/optical';output=root/'outputs/optical/summary'
    manifest=json.loads((source/'manifest.json').read_text())
    baseline=load_baseline(root/'docs/references'/manifest['workbook'])
    if baseline.source_sha256!=manifest['workbook_sha256']:raise ValueError('Stale optical baseline')
    model=OpticalModel(baseline);nominal=StudyCase(**manifest['nominal_instrument_case'])
    sizes=(1,5,10,100);colors=('#0072B2','#009E73','#E3B900','#7B3294')
    groups={k:[StudyCase(**{f:v for f,v in c.items() if f!='label'}) for c in values]
            for k,values in manifest['groups'].items()}
    groups['altitude']=[nominal]
    titles={'phase':'Fase','albedo':'Albedo','fov':'FOV','aperture':'Apertura',
            'velocity':'Velocidad transversal','altitude':'Referencia a 450 km'}
    fields={'phase':'phase_deg','albedo':'albedo','fov':'fov_deg','aperture':'aperture_m',
            'velocity':'transverse_speed_m_s','altitude':'observer_altitude_km'}
    units={'phase':'°','albedo':'','fov':'°','aperture':' mm','velocity':' km/s','altitude':' km'}
    factors={'aperture':1000,'velocity':.001}
    cache={}
    for cases in groups.values():
        for case in cases:
            for size in sizes:
                if (case,size) not in cache:
                    cache[case,size]=model.range_intervals(case,size/100,manifest['range_grid_m'])
    publication_style()
    max_distance=max(iv['upper_m']/1000 for ivs in cache.values() for iv in ivs)
    min_distance=min(iv['lower_m']/1000 for ivs in cache.values() for iv in ivs)
    for logarithmic in (False,True):
        fig,axes=plt.subplots(2,3,figsize=(17,11),layout='constrained')
        for ax,(group,cases) in zip(axes.flat,groups.items()):
            for j,case in enumerate(cases):
                for k,(size,color) in enumerate(zip(sizes,colors)):
                    y=j+(k-1.5)*.18
                    ivs=cache[case,size]
                    for iv in ivs:
                        lo,hi=iv['lower_m']/1000,iv['upper_m']/1000
                        ax.plot([lo,hi],[y,y],lw=4,color=color,solid_capstyle='butt')
                        ax.plot(lo,y,marker='o',ms=3,color=color,markeredgecolor='#555555',markeredgewidth=.4)
                        ax.plot(hi,y,marker='>' if iv['upper_censored'] else '|',ms=5,color=color)
                    if not ivs:ax.text(min_distance,y,'Sin intervalo',fontsize=7,color=color)
            labels=[f"{getattr(c,fields[group])*factors.get(group,1):g}{units[group]}" for c in cases]
            ax.set(yticks=range(len(cases)),yticklabels=labels,title=titles[group],
                   ylim=(len(cases)-.5,-.5),xlabel='Distancia [km]'+(' · escala logarítmica' if logarithmic else ' · escala lineal'))
            if logarithmic:
                ax.set_xscale('log');ax.set_xlim(min_distance*.7,max_distance*1.2)
                ax.xaxis.set_minor_locator(LogLocator(base=10,subs=np.arange(2,10)))
            else:
                ax.set_xlim(0,max_distance*1.05);ax.xaxis.set_minor_locator(AutoMinorLocator(5))
            ax.yaxis.set_minor_locator(MultipleLocator(.2))
            ax.tick_params(axis='y',which='minor',length=0)
            ax.set_axisbelow(True)
            ax.grid(which='major',linewidth=.5,color='#9DA5AE',alpha=.55)
            ax.grid(which='minor',linewidth=.3,color='#BFC5CC',alpha=.45)
        handles=[Line2D([0],[0],color=c,lw=5,label=f'{s} cm') for s,c in zip(sizes,colors)]
        fig.legend(handles=handles,loc='outside upper center',ncol=4,frameon=False,
                   title='TRACE — ventanas ópticas por tamaño de objeto',title_fontsize=17)
        fig.supxlabel('Cada barra va del mínimo al máximo elegible. Los huecos se conservan. Flecha: máximo censurado por el barrido.\n'
                      'Referencia: D=80 mm, FOV=14°, fase=60°, p=0,2, v⊥=5 km/s, 77 ms, 450 km. Incluye tránsitos parciales con SNR ≥ 5. Un parámetro cambia por panel.',fontsize=10)
        save_figure(fig,output,'trace_instrument_reference_sizes_1_5_10_100cm_windows_'+('log' if logarithmic else 'linear'))
    rows=[];interval_rows=[]
    for j,((case,size),ivs) in enumerate(cache.items(),1):
        lo=ivs[0]['lower_m']/1000 if ivs else None;hi=ivs[-1]['upper_m']/1000 if ivs else None
        rows.append([f'VIS-{j:03d}',size,case.phase_deg,case.albedo,case.fov_deg,case.aperture_m*1000,
            case.transverse_speed_m_s/1000,case.observer_altitude_km,baseline['t_int']*1000,
            baseline['FWC_high_gain'],len(ivs),';'.join(ivs[0]['lower_constraints']) if ivs else '',
            bool(ivs and ivs[-1]['upper_censored']),lo,hi])
        for k,iv in enumerate(ivs,1):interval_rows.append([f'VIS-{j:03d}',k,iv['lower_m']/1000,iv['upper_m']/1000,iv['upper_censored']])
    headers=['Caso visual','Diámetro [cm]','Fase [deg]','Albedo','FOV [deg]','Apertura [mm]',
             'Velocidad transversal [km/s]','Altitud observador [km]','Exposición [ms]','Full well [e-/px]',
             'Intervalos','Causa mínima','Máximo censurado','Alcance óptico mínimo [km]','Alcance óptico máximo [km]']
    with (source/'size_comparison_cases.csv').open('w',newline='') as f:
        writer=csv.writer(f,lineterminator='\n');writer.writerow(headers);writer.writerows(rows)
    excel=source/'TRACE_Resultados_Estudio_Optico.xlsx'
    wb=load_workbook(excel)
    for name,columns,values in [('TamanosComparados',headers,rows),('IntervalosTamanos',
        ['Caso visual','Intervalo','Mínimo [km]','Máximo [km]','Máximo censurado'],interval_rows)]:
        if name in wb:del wb[name]
        ws=wb.create_sheet(name);ws.append(columns)
        for row in values:ws.append(row)
        ws.freeze_panes='C2'
        table=Table(displayName=name,ref=ws.dimensions)
        table.tableStyleInfo=TableStyleInfo(name='TableStyleMedium2',showRowStripes=True);ws.add_table(table)
        for column in ws.columns:ws.column_dimensions[column[0].column_letter].width=25
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                if isinstance(cell.value,float):cell.number_format='0.00'
    wb.save(excel)
    nominal_path=root/'data/generated/trace_population_50000.csv';sha=hashlib.sha256(nominal_path.read_bytes()).hexdigest()
    population=load_population(nominal_path);diameters=population['diameter_m']*100
    bins=np.geomspace(1,np.nextafter(diameters.max(),np.inf),61)
    counts,edges=np.histogram(diameters,bins)
    subset=diameters[(diameters>=1)&(diameters<10)]
    zoom_counts,zoom_edges=np.histogram(subset,np.arange(1,10.125,.25))
    assert counts.sum()==50000 and zoom_counts.sum()==len(subset)
    fig,axes=plt.subplots(1,2,figsize=(12,4.7),layout='constrained')
    for ax,values,edge,title in zip(axes,(counts,zoom_counts),(edges,zoom_edges),
        ('Población completa · 50.000 objetos','Detalle 1–10 cm · '+f'{len(subset):,}'.replace(',','.')+' objetos')):
        ax.stairs(values,edge,fill=True,color='#0072B2',edgecolor='black',linewidth=.5)
        ax.set(xlabel='Diámetro equivalente [cm]',ylabel='Número de objetos por intervalo',title=title)
        ax.set_axisbelow(True);ax.grid(which='major',linewidth=.5,alpha=.4);ax.grid(which='minor',linewidth=.3,alpha=.3)
    axes[0].set_xscale('log');axes[0].set_xlabel('Diámetro equivalente [cm] · escala logarítmica')
    axes[1].set_xlim(1,10)
    fig.suptitle('TRACE — tamaños de la población nominal',fontsize=16)
    fig.supxlabel('Izquierda: 60 intervalos logarítmicos y todos los objetos. Derecha: intervalos de 0,25 cm; solo 1 ≤ d < 10 cm.\n'
                  'Conteos de registros, sin pesos estadísticos. Las alturas de ambos paneles usan anchos de intervalo diferentes.',fontsize=9)
    save_figure(fig,root/'outputs','trace_nominal_object_size_histogram')
    with (root/'data/generated/nominal_size_histogram.csv').open('w',newline='') as f:
        writer=csv.writer(f,lineterminator='\n');writer.writerow(['panel','lower_cm','upper_cm','objects'])
        for label,edge,values in [('full',edges,counts),('zoom_1_10cm',zoom_edges,zoom_counts)]:
            writer.writerows(zip([label]*len(values),edge[:-1],edge[1:],values))
    (output/'trace_instrument_reference_450_600_zenith_geometry.png').unlink(missing_ok=True)
    assert hashlib.sha256(nominal_path.read_bytes()).hexdigest()==sha
    audit={'cases':len(rows),'sizes_cm':sizes,'nominal_sha256_unchanged':sha,'histogram_count':int(counts.sum()),
           'histogram_zoom_count':int(zoom_counts.sum()),'histogram_max_cm':float(diameters.max()),
           'orbit_examples':[{"altitude_km":h,'period_minutes':2*np.pi/replace(nominal,observer_altitude_km=h).frame_rate_rad_s/60,
                              'rotation_deg_per_minute':replace(nominal,observer_altitude_km=h).frame_rate_rad_s*180/np.pi*60} for h in (450,)]}
    (source/'size_visualization_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
