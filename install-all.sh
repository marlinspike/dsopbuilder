#/bin/bash

python3 main.py settings azlogingov \
&& python3 main.py rke2 apply --project bb07 \
&& pushd working/dsop_rke2/bb07/ \
&& sleep 180 \
&& ./run_after_deploy.sh \
&& export KUBECONFIG=$(pwd)/rke2.kubeconfig \
&& echo "KUBECONFIG set to <$KUBECONFIG>" \
&& popd \
&& python3 main.py bb rke2