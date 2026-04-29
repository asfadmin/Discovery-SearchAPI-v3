# SearchAPI-v3


[![es](https://img.shields.io/badge/lang-es-yellow.svg)](./README.es.md)

SearchAPI-v3 is a wrapper around the [asf-search python module](https://github.com/asfadmin/Discovery-asf_search) using a serverless deployment with the FastAPI web framework and AWS lambda.

### Main Endpoints

<table>
  <thead>
    <tr>
      <th>Endpoint</th>
      <th>Description</th>
      <th>Methods</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>`/`</td>
      <td>server configuration info</td>
      <td>`GET`</td>
    </tr>
    <tr>
      <td>`/health`</td>
      <td>same as root `/`</td>
      <td>`GET`</td>
    </tr>
    <tr>
      <td>`/services/search/param`</td>
      <td>Search via any valid asf-search parameters</td>
      <td>`GET` `POST` `HEAD`</td>
    </tr>
    <tr>
      <td>`/services/search/baseline`</td>
      <td>Create a baseline stack based off a given reference and optional dataset</td>
      <td>`GET` `POST` `HEAD`</td>
    </tr>
  </tbody>
</table>

## Development

### Branching

<table>
  <thead>
    <tr>
      <th>Instance</th>
      <th>Branch</th>
      <th>Description, Instructions, Notes</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Features</td>
      <td>feat-*</td>
      <td>Always branch off dev, for new features</td>
    </tr>
    <tr>product_list with platform invalid
      <td>Issues</td>
      <td>bugfix-*</td>
      <td>Always branch off dev, for bugfixes</td>
    </tr>
    <tr>
      <td>development</td>
      <td>dev</td>
      <td>Beginning integration testing happens here, deploys to test-staging deployment</td>
    </tr>
    <tr>
      <td>testing</td>
      <td>test</td>
      <td>Only accepts merges from development, test deployment</td>
    </tr>
    <tr>
      <td>production staging and integration testing</td>
      <td>prod-staging</td>
      <td>Only accepts merges from testing, deploys to prod-staging deployment</td>
    </tr>
    <tr>
      <td>release</td>
      <td>prod</td>
      <td>only accepts merges from prod-staging, release branch, prod deployment</td>
    </tr>
  </tbody>
</table>

### Installation

To install locally run the following in a terminal (we highly recommend installing using a virtual environment)
```bash
pip install -r requirements.txt
pip install .
```

To install test requirements, run
```bash
pip install -r tests/requirements.txt
```

### Running Locally

To run the API locally run the following in a terminal
```bash
uvicorn src.SearchAPI.application:app --reload --port 8080
```
The api should now be available via your localhost at http://127.0.0.1:8080 and can be opened and queried with your browser or network tool of choice.




## Testing

## Running the Test Suite Locally 
After running the API (see `Running Locally` above), in order to run the test suite locally run the following:
```bash
pytest --api "http://127.0.0.1:8080" -n auto "tests/yml_tests/"
```

## Writing tests
Tests should be written to relevant subfolder & files in `/tests`

The test suite uses the `pytest-automation` pytest plugin which allows us to define and re-use input for test cases in the yaml format. Test cases are written to files in `tests/yml_tests/`, and reusable resources for those tests `tests/yml_tests/Resources/`.

```yaml

tests:
- Test Nisar Product L1 RSLC: # this is a test case
    product: NISAR_L1_PR_RSLC_087_039_D_114_2005_DHDH_A_20251102T222008_20251102T222017_T00407_N_P_J_001.yml # this file should be in `tests/yml_tests/Resources/`. See other yml files in the folder to see how you might structure the yml object
    product_level: L1

- Test Nisar Product L2 GSLC: # this is another test case
    product: NISAR_L2_PR_GSLC_087_039_D_112_2005_DHDH_A_20251102T221859_20251102T221935_T00407_N_F_J_001.yml
    product_level: L2
```

We can create the mapping from our yaml test cases in `tests/yml_tests/pytest-config.yml`, which will be used to call the desired python function in `tests/yml_tests/pytest-managers.py`

In `tests/yml_tests/pytest-config.yml`:
```yaml
- For running ASFProduct tests:
    required_keys: ['product', 'product_level'] # the keys the test case requires
    method: test_NISARProduct # the python function in pytest-managers.py that will be called
    required_in_title: Test Nisar Product # (OPTIONAL) will only run test cases defined with `Test Nisar Product` in the name, so the above two test cases would be run with our tests.
```


In `tests/yml_tests/pytest-managers.py`:
```python
def test_new_endpoint(**args) -> None: # Must match the name in pytest-config.yml like above for `method`
   test_new_endpoint(client=client, **args)
```
