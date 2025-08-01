# Para hallar % de cobertura el area debe estar en km2 lo que hace
# necesario un sistema de referencia lineal, tipo 'EPSG:32718'

""" Mantener las geometrías en un sistema de referencia de coordenadas geográficas 
(como WGS 84, con EPSG:4326) puede producir cálculos de área incorrectos debido 
a la naturaleza de estas proyecciones. Las coordenadas geográficas usan grados de 
latitud y longitud, que no representan distancias uniformes en la superficie de la Tierra. 
Esto significa que las distancias y áreas medidas en estos sistemas pueden ser distorsionadas, 
especialmente en regiones alejadas del ecuador.

Para realizar cálculos precisos de área y distancia, es necesario re-proyectar las geometrías 
a un sistema de referencia de coordenadas proyectadas. Estos sistemas utilizan unidades lineales 
como metros, lo que permite obtener medidas más precisas. """

import geopandas as gpd
import pandas as pd
import os

# Lista de empresas, tecnologías y tipos de cobertura
empresas = ['bitel', 'claro', 'entel', 'movistar']  # Lista de nombres de empresas
tecnologias = ['2g', '3g', '4g', '5g']  # Lista de tecnologías
#tecnologias = ['5g']  # Lista de tecnologías
tipos_cobertura = ['cobertura_adicional', 'cobertura_garantizada']  # Lista de tipos de cobertura
#tipos_cobertura = ['cobertura_garantizada']  # Lista de tipos de cobertura


# Directorio base
base_dir = '/Mapas inter-disueltos 2025-1/'

ruta_shp_ccpp_rural = '/CiudadesCcpp2023.shp'

ccpp_rural = gpd.read_file(ruta_shp_ccpp_rural)

ccpp_rural_km2 = ccpp_rural.to_crs('EPSG:32718')


# DataFrame (puro) acumulativo para todas las combinaciones
df_final_rural = ccpp_rural[['UBIGEO', 'DPTO', 'PROV', 'DIST', 'CCPP']].copy()



print(f'------------------------------')
print(f'Procesando data RURAL')
print(f'------------------------------')

for tecnologia in tecnologias:
    print(f'------------------------------')
    print(f'Procesando: {tecnologia}')
    print(f'------------------------------')
    for tipo_cobertura in tipos_cobertura:
        print(f'Procesando: {tipo_cobertura}')
        print(f'------------------------------')

        ruta_shp = os.path.join(base_dir, f"{tecnologia}-{tipo_cobertura}.shp")

        if not os.path.exists(ruta_shp):
            print(f'Archivo no encontrado: {ruta_shp}.')
            print(f'Saltando...')
            print(f'------------------------------')
            continue  # Salta al siguiente tipo de cobertura

        data = gpd.read_file(ruta_shp)
        data_km2 = data.to_crs('EPSG:32718')

        
        print(f'------------------------------------------------------------')
        print('Realizando intersección...')
        resultado_interseccion = gpd.overlay(ccpp_rural_km2, data_km2, how='intersection')
        print(' --> Intersección concluida')
        print(f'------------------------------------------------------------')
        print('Disolviendo valores únicos a nivel distrital')

        # Obtener valores únicos de departamento, provincia y distrito
        valores_unicos = resultado_interseccion.dissolve(by=['UBIGEO', 'DPTO', 'PROV', 'DIST', 'CCPP']).reset_index()
        valores_unicos[f'area_km2-{tecnologia}-{tipo_cobertura}'] = round(valores_unicos['geometry'].area / 1e6, 6)
        print(valores_unicos.columns)
        print(valores_unicos)

        # Crear un DataFrame para guardar en Excel
        datos_para_excel = valores_unicos[['UBIGEO', 'DPTO', 'PROV', 'DIST', 'CCPP', f'area_km2-{tecnologia}-{tipo_cobertura}']]

        # Merge con el DataFrame acumulativo
        df_final_rural = df_final_rural.merge(datos_para_excel, on=['UBIGEO', 'DPTO', 'PROV', 'DIST', 'CCPP'], how='left')

        # Renombrar UBIGEO_x a UBIGEO y eliminar UBIGEO_y si aparece
        df_final_rural.rename(columns={'UBIGEO_x': 'UBIGEO'}, inplace=True)
        df_final_rural.drop(columns=['UBIGEO_y'], errors='ignore', inplace=True)


        # Rellenar valores NaN con 0
        df_final_rural[f'area_km2-{tecnologia}-{tipo_cobertura}'].fillna(0, inplace=True)

# Guardar el DataFrame final en un solo archivo Excel
output_excel = os.path.join(base_dir, "area-cubierta-rural-2025-i.xlsx")
df_final_rural.to_excel(output_excel, index=False)

print(f'Archivo Excel consolidado guardado en: {output_excel}')