# rocy9-base

systemdを動作させるためには、以下のオプションが必要です。

```
$ sudo docker run -d -it --rm --privileged --cap-add=SYS_ADMIN --name rocky9 local/rocky9-base
```
