# keycloak

- https://www.keycloak.org/

## console

```
bash -c "source laborc && labo-ansible-playbook keycloak-docker"
```

http://192.168.10.121:8080/admin

- 参考
  - [KeyCloak を使って SAML の IdP サーバーをローカルで立ち上げる方法](https://qiita.com/ymstshinichiro/items/f0b231d4bf5d020f7e3b)
  - [【Keycloak】Apache の VirtualHost で分けられた複数のサイトをまとめてシングルサインオンしよう]'https://qiita.com/thirdpenguin/items/1136c755560eea51b5b1)
  - [mod_auth_mellon を使ってみた](https://qiita.com/aimoto/items/89ba104db85a2b89fa67)
  - [3.2. Apache HTTPD モジュール mod_auth_mellon](https://access.redhat.com/documentation/ja-jp/red_hat_single_sign-on/7.4/html/securing_applications_and_services_guide/_mod_auth_mellon)
  - [OpenStack: Setting Up Mellon](https://docs.openstack.org/keystone/latest/admin/federation/configure_federation.html#setting-up-mellon)
