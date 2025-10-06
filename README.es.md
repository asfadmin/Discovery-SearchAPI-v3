# SearchAPI-v3

[![en](https://img.shields.io/badge/lang-en-red.svg)](./README.md)


SearchAPI-v3 es un contenedor alrededor del [módulo de python asf-search](https://github.com/asfadmin/Discovery-asf_search) utilizando un despliegue sin servidor con el framework FastAPI y AWS Lambda.

### Endpoints principales

<table>
  <thead>
    <tr>
      <th>Endpoint</th>
      <th>Descripción</th>
      <th>Métodos</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>`/`</td>
      <td>Información de configuración del servidor</td>
      <td>`GET`</td>
    </tr>
    <tr>
      <td>`/health`</td>
      <td>igual que root `/`</td>
      <td>`GET`</td>
    </tr>
    <tr>
      <td>`/services/search/param`</td>
      <td>Búsqueda mediante cualquier parámetro válido de asf-search</td>
      <td>`GET` `POST` `HEAD`</td>
    </tr>
    <tr>
      <td>`/services/search/baseline`</td>
      <td>Crear un stack de línea base a partir de una referencia dada y dataset opcional</td>
      <td>`GET` `POST` `HEAD`</td>
    </tr>
  </tbody>
</table>

## Desarrollo

### Ramificación

<table>
  <thead>
    <tr>
      <th>Instancia</th>
      <th>Rama</th>
      <th>Descripción, Instrucciones, Notas</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Características</td>
      <td>feat-*</td>
      <td>Siempre crear a partir de dev, para nuevas funciones</td>
    </tr>
    <tr>
      <td>Problemas</td>
      <td>bugfix-*</td>
      <td>Siempre crear a partir de dev, para correcciones</td>
    </tr>
    <tr>
      <td>desarrollo</td>
      <td>dev</td>
      <td>Aquí comienza la integración inicial; despliega en el entorno test-staging.</td>
    </tr>
    <tr>
      <td>pruebas</td>
      <td>test</td>
      <td>Solo acepta fusiones desde la rama development; despliegue en el entorno de prueba</td>
    </tr>
    <tr>
      <td>preproducción e integración</td>
      <td>prod-staging</td>
      <td>Solo acepta fusiones desde la rama testing; despliegue en el entorno prod-staging</td>
    </tr>
    <tr>
      <td>release</td>
      <td>prod</td>
      <td>Solo acepta fusiones desde la rama prod-staging; rama de release, despliegue a producción</td>
    </tr>
  </tbody>
</table>

### Instalación

Para instalar localmente, ejecute lo siguiente en una terminal (se recomienda altamente hacerlo en un entorno virtual):
```bash
pip install -r requirements.txt
pip install .
```

Para instalar los requisitos de prueba:
```bash
pip install -r tests/requirements.txt
```

### Ejecución local

Para ejecutar la API localmente, ejecute lo siguiente en una terminal:
```bash
uvicorn src.SearchAPI.application:app --reload --port 8080
```
La API ahora debería estar disponible en su localhost en http://127.0.0.1:8080 y se puede consultar con su navegador o herramienta de red de preferencia.




## Pruebas

### Ejecutar el conjunto de pruebas localmente
Después de ejecutar la API (vea `Ejecución local` arriba), para correr la suite de pruebas localmente ejecute:
```bash
pytest --api "http://127.0.0.1:8080" -n auto "tests/yml_tests/"
```

### Escribir pruebas
Las pruebas deben escribirse en las subcarpetas y archivos relevantes en `/tests`.

La suite de pruebas usa el plugin `pytest-automation` que permite definir y reutilizar entradas para casos de prueba en formato yaml. Los casos de prueba se escriben en archivos dentro de `tests/yml_tests/`, y los recursos reutilizables en `tests/yml_tests/Resources/`.

```yaml

tests:
- Test Nisar Product L1 RSLC: # este es un caso de prueba
   product: NISAR_L1_PR_RSLC_087_039_D_114_2005_DHDH_A_20251102T222008_20251102T222017_T00407_N_P_J_001.yml # este archivo debe estar en `tests/yml_tests/Resources/`. Vea otros archivos yml en la carpeta para observar cómo podría estructurar el objeto yml
   product_level: L1

- Test Nisar Product L2 GSLC: # este es otro caso de prueba
    product: NISAR_L2_PR_GSLC_087_039_D_112_2005_DHDH_A_20251102T221859_20251102T221935_T00407_N_F_J_001.yml
    product_level: L2
```

Podemos crear el mapeo desde nuestros casos de prueba yaml en `tests/yml_tests/pytest-config.yml`, que se usará para llamar la función de python deseada en `tests/yml_tests/pytest-managers.py`.

En `tests/yml_tests/pytest-config.yml`:
```yaml
- Para ejecutar pruebas de ASFProduct:
    required_keys: ['product', 'product_level'] # las claves que requiere el caso de prueba
    method: test_NISARProduct # la función de Python en pytest-managers.py que será llamada
    required_in_title: Test Nisar Product # (OPCIONAL) solo ejecutará los casos de prueba que tengan `Test Nisar Product` en el nombre; por ello, los dos casos anteriores se ejecutarían con nuestras pruebas.
```

En `tests/yml_tests/pytest-managers.py`:

```python
def test_new_endpoint(client=None, **args) -> None:
    test_new_endpoint(client=client, **args)
```
