# Merge Requirements:
The following requirements must be met for your pull request to be considered for review & merging. Until these requirements are met please mark the pull request as a draft.

## Purpose
Why is this pull request necessary? Provide a reference to a related issue in this repository that your pull request addresses (if applicable).

## Description
A brief description of the changes proposed in the pull request. If there are any changes to packaging requirements please list them. If it's a new endpoint list:
- Supported HTTP methods
- input params
- output
- errors it can raise

## Snippet
If the pull request provides a new feature, provide an example demonstrating the use-case(s) for this pull request (If applicable).

For example, if you are adding a new endpoint, show how we might call it and what kind of output we could expect:
``` bash
curl 'http://127.0.0.1:8080/services/utils/useful_new_endpoint?param1=value1&param2=value2'
```

If it modifies an existing endpoint (like a new output type for `/services/search/param`) show and example of what the output would look like.

## Error/Warning/Regression Free
Your code runs without any unhandled errors, warnings, or regressions

## Unit Tests

You have added unit tests to the test suite see the [README Testing section](https://github.com/asfadmin/Discovery-SearchAPI-v3/tree/dev?tab=readme-ov-file#writing-tests) for an overview on adding tests to the test suite.

## Target Merge Branch
Your pull request targets the `master` branch


***

### Checklist
- [ ] Purpose
- [ ] Description
- [ ] Snippet
- [ ] Error/Warning/Regression Free
- [ ] Unit Tests
- [ ] Target Merge Branch