# aws-greengrass-streammanager-python-segfault-repro
Reproducibility repo for Greengrass V2 StreamManager Python SDK SegFault


## Reproduction

1. Deploy this component to the test account and deploy to a test Greengrass instance (or otherwise get this component loaded into a running Greengrass instance)

  ```bash
  export AWS_PROFILE=<YOUR TARGET AWS ACCOUNT>
  export VERSION=1.0.0-test.0
  python3 scripts/build.py --version $VERSION
  python3 scripts/deploy.py --version $VERSION
  ```

2. Once the deployment is live, create an no-op deployment

3. Observe the repro-component logs for a seg-fault during deployment.
