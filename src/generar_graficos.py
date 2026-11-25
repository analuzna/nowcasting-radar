import pyart
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import numpy as np
from netCDF4 import num2date
from IPython.display import display, clear_output
import ipywidgets as widgets
from pathlib import Path


# carpeta_entrada = Path('/home/ana_luz/Tesis/DATOS_RADAR/20241212/')

# archivos_nc = sorted(carpeta_entrada.glob('*.nc'))

def graficar_radar(archivo, campo='COLMAX', vmin=-30, vmax=70):
    radar = pyart.io.read(str(archivo))

    if campo not in radar.fields:
        print(f"El archivo no contiene el campo {campo}.")
        print("Campos disponibles:", list(radar.fields))
        return

    lat0 = radar.latitude['data'][0]
    lon0 = radar.longitude['data'][0]

    # Extensión aproximada de 100 km alrededor del radar
    km_to_deg = 100 / 111
    deg_lon = km_to_deg / np.cos(np.deg2rad(lat0))

    projection = ccrs.PlateCarree()
    fig, ax = plt.subplots(
        figsize=(8, 7),
        subplot_kw={'projection': projection}
    )

    display_radar = pyart.graph.RadarMapDisplay(radar)

    display_radar.plot_ppi_map(
        campo,
        0,
        vmin=vmin,
        vmax=vmax,
        cmap='grc_th',
        projection=projection,
        ax=ax,
        lat_0=lat0,
        lon_0=lon0
    )

    ax.set_extent(
        [
            lon0 - deg_lon,
            lon0 + deg_lon,
            lat0 - km_to_deg,
            lat0 + km_to_deg
        ],
        crs=projection
    )

    dt = num2date(
        radar.time['data'][0],
        units=radar.time['units']
    )

    ax.set_title(f'{campo} — {dt.strftime("%Y-%m-%d %H:%M:%S UTC")}')
    plt.tight_layout()
    plt.show()

    return radar