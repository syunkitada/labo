package main

import (
	"flag"
	"fmt"
	"time"

	v1 "k8s.io/api/core/v1"
	meta_v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/fields"
	"k8s.io/apimachinery/pkg/util/runtime"
	"k8s.io/apimachinery/pkg/util/wait"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/tools/cache"
	"k8s.io/client-go/tools/clientcmd"
	"k8s.io/client-go/util/workqueue"
	"k8s.io/klog/v2"
)

type Controller struct {
	indexer  cache.Indexer
	queue    workqueue.RateLimitingInterface
	informer cache.Controller
}

func NewController(queue workqueue.RateLimitingInterface, indexer cache.Indexer, informer cache.Controller) *Controller {
	return &Controller{
		informer: informer,
		indexer:  indexer,
		queue:    queue,
	}
}

func (c *Controller) processNextItem() bool {
	// queueから新しいアイテムを取得するまで待つ
	key, quit := c.queue.Get()
	if quit {
		return false
	}
	// key単位でアイテムはブロックされており他のworkerは触ることができない
	// Doneすることでこのkeyのアイテムは解放される
	defer c.queue.Done(key)

	// なんらかの処理
	err := c.syncToStdout(key.(string))

	// errがあった場合はなんらかの処理を行う
	c.handleErr(err, key)
	return true
}

// ただ出力するだけ
func (c *Controller) syncToStdout(key string) error {
	obj, exists, err := c.indexer.GetByKey(key)
	if err != nil {
		klog.Errorf("Fetching object with key %s from store failed with %v", key, err)
		return err
	}

	if exists {
		fmt.Printf("Pod %s does not exist anymore\n", key)
	} else {
		pod, ok := obj.(*v1.Pod)
		if ok {
			fmt.Printf("Sync/Add/Update for Pod %s\n", pod.GetName())
		} else if pod == nil {
			fmt.Printf("pod is nil: key=%s\n", key)
		} else {
			fmt.Printf("Unexpected object is found: key=%s, object=%v\n", key, obj)
		}
	}

	return nil
}

// errorが発生していた場合は後でretryする
func (c *Controller) handleErr(err error, key interface{}) {
	if err == nil {
		// 同期に成功した場合(errがない場合)は、keyのAddRateLimited historyを忘れます
		// これにより、再度同じkeyは処理しなくなる
		c.queue.Forget(key)
		return
	}

	// errがある場合は、5回までリトライします
	if c.queue.NumRequeues(key) < 5 {
		klog.Infof("Error syncing pod %v: %v", key, err)

		// 再度keyをqueueに詰め込みます(一定時間後にretryします)
		c.queue.AddRateLimited(key)
		return
	}

	// 一定回数以上失敗した場合は、あきらめます
	c.queue.Forget(key)
	runtime.HandleError(err)
	klog.Infof("Dropping pod %q out of the queue: %v", key, err)
}

func (c *Controller) Run(workers int, stopCh chan struct{}) {
	defer runtime.HandleCrash()

	defer c.queue.ShutDown()
	klog.Info("Starting Pod controller")

	go c.informer.Run(stopCh)

	if !cache.WaitForCacheSync(stopCh, c.informer.HasSynced) {
		runtime.HandleError(fmt.Errorf("Timed out waiting for caches to sync"))
		return
	}

	for i := 0; i < workers; i++ {
		go wait.Until(c.runWorker, time.Second, stopCh)
	}

	<-stopCh
	klog.Info("Stopping Pod controller")
}

func (c *Controller) runWorker() {
	for c.processNextItem() {
	}
}

func main() {
	var kubeconfig string
	var master string

	flag.StringVar(&kubeconfig, "kubeconfig", "", "absolute path to the kubeconfig file")
	flag.StringVar(&master, "master", "", "master url")
	flag.Parse()

	config, err := clientcmd.BuildConfigFromFlags(master, kubeconfig)
	if err != nil {
		klog.Fatal(err)
	}

	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		klog.Fatal(err)
	}

	// pod watcherを作成します
	podListWatcher := cache.NewListWatchFromClient(clientset.CoreV1().RESTClient(), "pods", v1.NamespaceDefault, fields.Everything())

	// workqueueを作成します
	queue := workqueue.NewRateLimitingQueue(workqueue.DefaultControllerRateLimiter())

	// indexerとinformerを作成します
	// cacheが更新されたときに、そのpodのkeyはworkqueueに追加されます
	indexer, informer := cache.NewIndexerInformer(podListWatcher, &v1.Pod{}, 0, cache.ResourceEventHandlerFuncs{
		AddFunc: func(obj interface{}) {
			key, err := cache.MetaNamespaceKeyFunc(obj)
			if err == nil {
				queue.Add(key)
			}
		},
		UpdateFunc: func(old interface{}, new interface{}) {
			key, err := cache.MetaNamespaceKeyFunc(new)
			if err == nil {
				queue.Add(key)
			}
		},
		DeleteFunc: func(obj interface{}) {
			// IndexerInformer は delta queueを利用します
			// そのため、deletesのためにこのkeyを使う必要があります
			key, err := cache.DeletionHandlingMetaNamespaceKeyFunc(obj)
			if err == nil {
				queue.Add(key)
			}
		},
	}, cache.Indexers{})

	controller := NewController(queue, indexer, informer)

	// 初回の同期のために暖気する
	// 仮に最後のrunでmypodを知っていたとし、キャッシュにそれを追加します
	// もし、このpodがいなければ、cacheが同期された後に削除のためにコントローラに通知されます
	indexer.Add(&v1.Pod{
		ObjectMeta: meta_v1.ObjectMeta{
			Name:      "mypod",
			Namespace: v1.NamespaceDefault,
		},
	})

	// コントローラを開始します
	stop := make(chan struct{})
	defer close(stop)
	go controller.Run(1, stop)

	// Wait forever
	select {}
}
