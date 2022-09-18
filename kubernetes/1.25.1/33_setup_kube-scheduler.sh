#!/bin/bash -x

source envrc

cd $K8S_ASSETS_DIR
cp kube-scheduler.kubeconfig $VAR_DIR
cd -

cat <<EOF | tee ${ETC_DIR}/kube-scheduler.yaml
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
clientConnection:
  kubeconfig: "${VAR_DIR}/kube-scheduler.kubeconfig"
leaderElection:
  leaderElect: true
EOF


for pid in `ps ax | grep scheduler | grep -v .sh | awk '{print $1}'`
do
    kill $pid
done

cd $SRC_DIR
go run -mod vendor cmd/kube-scheduler/scheduler.go \
  --config=${ETC_DIR}/kube-scheduler.yaml \
  --v=2 \
  1>$LOG_DIR/kube-scheduler.log 2>&1 &
