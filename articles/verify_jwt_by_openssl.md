---
title: JWTの署名をOpenSSLコマンドで検証する
tags: Firebase JWT openssl 暗号
author: yyu
slide: false
---
# はじめに

JWTは[Firebase](https://firebase.google.com/)などで利用される、改竄防止の署名やメッセージ認証コードを付与したJSONをBase64エンコードしたうえでヘッダーを付けたデータ構造である。通常署名やメッセージ認証コードの検証は専用のSDKやライブラリーで行うことがほとんどであり、検証ロジックを安易に自作するべきではないが、デバッグ目的ではコマンドラインツールで検証できると役に立つことがある。この記事ではFirebaseの認証において発行されるJWTを例として、Pythonなどのプログラム言語を利用せずにOpenSSLや`base64`などのコマンドラインツールのみを使って気合で署名を検証する方法を紹介する。

## 使ったOpenSSLのバージョン情報

```console
$ openssl version
OpenSSL 1.1.1d  10 Sep 2019
```

# FirebaseのJWTの取得

実際に手元にFirebaseのアカウントなどがなくても、https://github.com/firebase/firebaseui-web#demo :point_left: ここのページからリンクされているデモアプリからJWTを取得できる。

<img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/7f034fa7-877c-92e3-92a9-781183a5be32.png" width="60%">

筆者はとりあえずGoogleアカウントと連携してみたが、成功すると次のように表示される。

<img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/14851768-d40c-1313-f134-7a2f80959833.png" width="60%">

この画面で、ChromeなどWebブラウザーのコンソールから次のようなJavaScriptを実行するとJWTを得ることができる。

```javascript
firebase.auth().currentUser.getIdToken(/* forceRefresh */ true).then(function(idToken) {
  console.log(idToken);
});
```

<img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/45efb7fb-f55f-68e1-16b6-54569a0d1dbc.png" width="60%">


```:JWT
eyJhbGciOiJSUzI1NiIsImtpZCI6IjFmODhiODE0MjljYzQ1MWEzMzVjMmY1Y2RiM2RmYjM0ZWIzYmJjN2YiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoi5ZCJ5p2R5YSqIiwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hLS9BT2gxNEdpWnp0M2o5ajRmNzRTYldqaTFMaHhmTWxOTzZlYXFyS2NnM2tSWkxRPXM5Ni1jIiwiaXNzIjoiaHR0cHM6Ly9zZWN1cmV0b2tlbi5nb29nbGUuY29tL2Zpci11aS1kZW1vLTg0YTZjIiwiYXVkIjoiZmlyLXVpLWRlbW8tODRhNmMiLCJhdXRoX3RpbWUiOjE1ODUwNjcyODIsInVzZXJfaWQiOiJlOFBjbXlKU0dmaEMwbGJIZDZSQWlFcG94MXYxIiwic3ViIjoiZThQY215SlNHZmhDMGxiSGQ2UkFpRXBveDF2MSIsImlhdCI6MTU4NTA2NzUxMSwiZXhwIjoxNTg1MDcxMTExLCJlbWFpbCI6Inl5dUBtZW50YWwucG9rZXIiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6eyJnb29nbGUuY29tIjpbIjEwMjEyMTUzOTY5Njc1NTExMDg0MyJdLCJlbWFpbCI6WyJ5eXVAbWVudGFsLnBva2VyIl19LCJzaWduX2luX3Byb3ZpZGVyIjoiZ29vZ2xlLmNvbSJ9fQ.NiPnBsPrebR9GGGgJrfRUja4o34JxqV-HbE-uHGbd15kU0O6re7G8K4cfPJtoK0D2ns9oAusI8qGN7fhS0o9CfxLim3sHtB2ZWyy4t3Lkcj6rb0ixTdoNiKvhlozc2vBwOoq3lB-Rr4MieuJ30qYLO07Kl_910FqRw6hSrTlMyEP1G1ozBgljF_GesttJEOLhE975T3yPuqLVoYKMNEqCscQqZkb9J6W9nIxZracQFk1-99o4_SSKBUKqr8oeTg0xqjqTnvsJ3khvyzy70P3e3tOfyuV-nrFDBUuMPBk_F9scaJNDFuSGQzVhHaT4eOXsXxEJ3M6FX8Dj9dOK19ppg
```

こうしてFirebaseのJWTを入手することができた。JWTはBase64エンコードされたJSONのヘッダーとボディ部があり、最後に署名（またはメッセージ認証コード）の3つが`.`で連結されているため、`.`で区切って`base64 -D`で戻せばよい。

```console
$ for i in {1,2}; do
  raw=`echo "eyJhbGciOiJSUzI1NiIsImtpZCI6IjFmODhiODE0MjljYzQ1MWEzMzVjMmY1Y2RiM2RmYjM0ZWIzYmJjN2YiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoi5ZCJ5p2R5YSqIiwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hLS9BT2gxNEdpWnp0M2o5ajRmNzRTYldqaTFMaHhmTWxOTzZlYXFyS2NnM2tSWkxRPXM5Ni1jIiwiaXNzIjoiaHR0cHM6Ly9zZWN1cmV0b2tlbi5nb29nbGUuY29tL2Zpci11aS1kZW1vLTg0YTZjIiwiYXVkIjoiZmlyLXVpLWRlbW8tODRhNmMiLCJhdXRoX3RpbWUiOjE1ODUwNjcyODIsInVzZXJfaWQiOiJlOFBjbXlKU0dmaEMwbGJIZDZSQWlFcG94MXYxIiwic3ViIjoiZThQY215SlNHZmhDMGxiSGQ2UkFpRXBveDF2MSIsImlhdCI6MTU4NTA2NzUxMSwiZXhwIjoxNTg1MDcxMTExLCJlbWFpbCI6Inl5dUBtZW50YWwucG9rZXIiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6eyJnb29nbGUuY29tIjpbIjEwMjEyMTUzOTY5Njc1NTExMDg0MyJdLCJlbWFpbCI6WyJ5eXVAbWVudGFsLnBva2VyIl19LCJzaWduX2luX3Byb3ZpZGVyIjoiZ29vZ2xlLmNvbSJ9fQ.NiPnBsPrebR9GGGgJrfRUja4o34JxqV-HbE-uHGbd15kU0O6re7G8K4cfPJtoK0D2ns9oAusI8qGN7fhS0o9CfxLim3sHtB2ZWyy4t3Lkcj6rb0ixTdoNiKvhlozc2vBwOoq3lB-Rr4MieuJ30qYLO07Kl_910FqRw6hSrTlMyEP1G1ozBgljF_GesttJEOLhE975T3yPuqLVoYKMNEqCscQqZkb9J6W9nIxZracQFk1-99o4_SSKBUKqr8oeTg0xqjqTnvsJ3khvyzy70P3e3tOfyuV-nrFDBUuMPBk_F9scaJNDFuSGQzVhHaT4eOXsXxEJ3M6FX8Dj9dOK19ppg" | cut -d"." -f"$i"`
  echo "$raw==" | base64 -D | jq
done
```

```json
{
  "alg": "RS256",
  "kid": "1f88b81429cc451a335c2f5cdb3dfb34eb3bbc7f",
  "typ": "JWT"
}
{
  "name": "吉村優",
  "picture": "https://lh3.googleusercontent.com/a-/AOh14GiZzt3j9j4f74SbWji1LhxfMlNO6eaqrKcg3kRZLQ=s96-c",
  "iss": "https://securetoken.google.com/fir-ui-demo-84a6c",
  "aud": "fir-ui-demo-84a6c",
  "auth_time": 1585067282,
  "user_id": "e8PcmyJSGfhC0lbHd6RAiEpox1v1",
  "sub": "e8PcmyJSGfhC0lbHd6RAiEpox1v1",
  "iat": 1585067511,
  "exp": 1585071111,
  "email": "yyu@mental.poker",
  "email_verified": true,
  "firebase": {
    "identities": {
      "google.com": [
        "102121539696755110843"
      ],
      "email": [
        "yyu@mental.poker"
      ]
    },
    "sign_in_provider": "google.com"
  }
}
```

最初のJSONであるヘッダー部を見ると`"alg": "RS256"`となっていることから、このJWTはRSAとSHA256を利用していると分かる。

# 公開鍵の取得

[Firebaseのマニュアル](https://firebase.google.com/docs/auth/admin/verify-id-tokens?hl=ja#verify_id_tokens_using_a_third-party_jwt_library)において、FirebaseのSDKではない方法で署名を検証するにはhttps://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com :point_left: から公開鍵をもってこいと書かれている。公開鍵は次のようなJSON形式である。

```json
{
  "82e6b1c921fa86770f3d50c12c15d6eaca8f0d35": "-----BEGIN CERTIFICATE-----\nMIIDHDCCAgSgAwIBAgIIHP/TdzppHAAwDQYJKoZIhvcNAQEFBQAwMTEvMC0GA1UE\nAxMmc2VjdXJldG9rZW4uc3lzdGVtLmdzZXJ2aWNlYWNjb3VudC5jb20wHhcNMjAw\nMzEwMDkxOTU0WhcNMjAwMzI2MjEzNDU0WjAxMS8wLQYDVQQDEyZzZWN1cmV0b2tl\nbi5zeXN0ZW0uZ3NlcnZpY2VhY2NvdW50LmNvbTCCASIwDQYJKoZIhvcNAQEBBQAD\nggEPADCCAQoCggEBALiBOk5gXVtUm4kOp9Nn+vw3GpZBQ//5vMdwA8x8cetuOVuo\n0bBbMNaP+QW9l1reIckB/rvDqMpKdIFF877pJbUSPCZemx/hiKbie2GzoZptRzJc\nJ7NTH0+oPvqOkUIMLfiL5J6fCDtCtpXVWwEBTPwZLBwmo+JnIEadVyBgSl64xMUn\nr5dAkCFOmjPjN5RIYYT0ced3zU5kV2ewEVazSf087gWR/RSJ0OXbd9+iUXtNZbQG\ntkZGCDfkJT1IGzdB03f64hWaedwyOAo/IFApKQwF1vCt6mAtBjjcheXRW1E1ZGml\nWbiPBs4Pe5t7d2ARRo0a3xFGjJNRDpSPfl2WIGkCAwEAAaM4MDYwDAYDVR0TAQH/\nBAIwADAOBgNVHQ8BAf8EBAMCB4AwFgYDVR0lAQH/BAwwCgYIKwYBBQUHAwIwDQYJ\nKoZIhvcNAQEFBQADggEBADYbilO0mB3qAalDW5tBkLyJL9OIbYFhRDNpPTm9gvpL\nksdpQGUG5G/0c+4csmn7/zk4aTiymsdo+oN/gS/bs+iXSTJw6K77j14n/XFohWTQ\nhnLEFo0pbA42x5h1dMkLfLOC2iIIm8lgvAh880m1hC/NZS0RKsofCohYY5Mu2arY\neJXiogvO7TVwEfW2ZcE4jOnwtMnXgyn6Hu5azEHI9rIVflTEl+o2CjEMoUOnm4Ib\nwUEQwlxa9SDa/2COiCrByvwzkKypbaAHGMV1/+sJ8Yaj9fF34yuWQOBDKF4/frnc\nTfYUMgCTepr5VIuJdSVCzEpaRr5IBqCu27sM6kJsWxM=\n-----END CERTIFICATE-----\n",
  "1f88b81429cc451a335c2f5cdb3dfb34eb3bbc7f": "-----BEGIN CERTIFICATE-----\nMIIDHDCCAgSgAwIBAgIIWbF+OhsQGJIwDQYJKoZIhvcNAQEFBQAwMTEvMC0GA1UE\nAxMmc2VjdXJldG9rZW4uc3lzdGVtLmdzZXJ2aWNlYWNjb3VudC5jb20wHhcNMjAw\nMzE4MDkxOTU1WhcNMjAwNDAzMjEzNDU1WjAxMS8wLQYDVQQDEyZzZWN1cmV0b2tl\nbi5zeXN0ZW0uZ3NlcnZpY2VhY2NvdW50LmNvbTCCASIwDQYJKoZIhvcNAQEBBQAD\nggEPADCCAQoCggEBANZRuU1SzL8TFi3wN0A7ftX3ziJsNPgihT5f+oFzCxnnKRMF\nC2bT3wG5kY/j5hdi+42HyIglpLuTCeJyjtmIkH25zIG9anb5RXx8ZajTV36boIXo\n+npDA5enYGUa4lTS5UJUN09UXW0dQBZR7XZYeYy9LpZhYXeinXI6sY5crjDmaMsf\nnv56SN1CFRf0gGgLES+APjdjpMKYyiXrswNJmp3HB+7hBaEFpGvmyIdc5U2fM0Ps\nRxBENtbRbl3z2HjS++hSPWfl9Etiag7NMpcQ7olUP1yORCs35ywNQULnUw2qayur\nB44Ig/Cr3tl6XlOaai9sLDEYwaIgKsIzrZ/fQkUCAwEAAaM4MDYwDAYDVR0TAQH/\nBAIwADAOBgNVHQ8BAf8EBAMCB4AwFgYDVR0lAQH/BAwwCgYIKwYBBQUHAwIwDQYJ\nKoZIhvcNAQEFBQADggEBAGtw2Xbfpl7O3oda7tIldxbJyXd4NbWT8NUdf1mhKgA6\n1sCWSd0fUxRu5Puv+nX7Nh6g6O7M44WgQnGIgba0gYL7pl3luNFjXgukAxfYf2LP\nq2Y/dnPWaK+5JErVfj9+fIyWzP43xaKx1S3nMKCGh3Gm9lhYxfSUKgNwxgI4xvDG\nP5g6lBLKfpdN76TS7bKQtN0ZktmhdpUwRnffWAaS2SG1JtJ0Bu/diOO38rS0yyQY\nhg0A4gHQcuw5VVINHpKnieAJ1GnaIpgHqwDZehs5hSIPiOvGgLSvctacsPqfbxtP\nGGbU/SsMNNE90PMC+RHecmuCvsDJfSVWkYV6T8wx3HM=\n-----END CERTIFICATE-----\n"
}
```

前述したJWTのヘッダー部分には`kid`というフィールドがあり、これは公開鍵のIDを示している。`1f88b81429cc451a335c2f5cdb3dfb34eb3bbc7f`となっているので、これに該当する上から二番目の公開鍵をダウンロードすればよい。ダブルクォートの部分をそのまま`echo`に突っ込んで公開鍵`google_cert.pem`をつくる。

```console
$ echo "-----BEGIN CERTIFICATE-----\nMIIDHDCCAgSgAwIBAgIIWbF+OhsQGJIwDQYJKoZIhvcNAQEFBQAwMTEvMC0GA1UE\nAxMmc2VjdXJldG9rZW4uc3lzdGVtLmdzZXJ2aWNlYWNjb3VudC5jb20wHhcNMjAw\nMzE4MDkxOTU1WhcNMjAwNDAzMjEzNDU1WjAxMS8wLQYDVQQDEyZzZWN1cmV0b2tl\nbi5zeXN0ZW0uZ3NlcnZpY2VhY2NvdW50LmNvbTCCASIwDQYJKoZIhvcNAQEBBQAD\nggEPADCCAQoCggEBANZRuU1SzL8TFi3wN0A7ftX3ziJsNPgihT5f+oFzCxnnKRMF\nC2bT3wG5kY/j5hdi+42HyIglpLuTCeJyjtmIkH25zIG9anb5RXx8ZajTV36boIXo\n+npDA5enYGUa4lTS5UJUN09UXW0dQBZR7XZYeYy9LpZhYXeinXI6sY5crjDmaMsf\nnv56SN1CFRf0gGgLES+APjdjpMKYyiXrswNJmp3HB+7hBaEFpGvmyIdc5U2fM0Ps\nRxBENtbRbl3z2HjS++hSPWfl9Etiag7NMpcQ7olUP1yORCs35ywNQULnUw2qayur\nB44Ig/Cr3tl6XlOaai9sLDEYwaIgKsIzrZ/fQkUCAwEAAaM4MDYwDAYDVR0TAQH/\nBAIwADAOBgNVHQ8BAf8EBAMCB4AwFgYDVR0lAQH/BAwwCgYIKwYBBQUHAwIwDQYJ\nKoZIhvcNAQEFBQADggEBAGtw2Xbfpl7O3oda7tIldxbJyXd4NbWT8NUdf1mhKgA6\n1sCWSd0fUxRu5Puv+nX7Nh6g6O7M44WgQnGIgba0gYL7pl3luNFjXgukAxfYf2LP\nq2Y/dnPWaK+5JErVfj9+fIyWzP43xaKx1S3nMKCGh3Gm9lhYxfSUKgNwxgI4xvDG\nP5g6lBLKfpdN76TS7bKQtN0ZktmhdpUwRnffWAaS2SG1JtJ0Bu/diOO38rS0yyQY\nhg0A4gHQcuw5VVINHpKnieAJ1GnaIpgHqwDZehs5hSIPiOvGgLSvctacsPqfbxtP\nGGbU/SsMNNE90PMC+RHecmuCvsDJfSVWkYV6T8wx3HM=\n-----END CERTIFICATE-----\n" \
 > google_cert.pem
```

この`google_cert.pem`をOpenSSLの`x509`コマンドで表示させると次のようになる。

```console
$ openssl x509 -in google_cert.pem -text
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number: 6463085728280615058 (0x59b17e3a1b101892)
        Signature Algorithm: sha1WithRSAEncryption
        Issuer: CN = securetoken.system.gserviceaccount.com
        Validity
            Not Before: Mar 18 09:19:55 2020 GMT
            Not After : Apr  3 21:34:55 2020 GMT
        Subject: CN = securetoken.system.gserviceaccount.com
        Subject Public Key Info:
            Public Key Algorithm: rsaEncryption
                RSA Public-Key: (2048 bit)
                Modulus:
                    00:d6:51:b9:4d:52:cc:bf:13:16:2d:f0:37:40:3b:
                    7e:d5:f7:ce:22:6c:34:f8:22:85:3e:5f:fa:81:73:
                    0b:19:e7:29:13:05:0b:66:d3:df:01:b9:91:8f:e3:
                    e6:17:62:fb:8d:87:c8:88:25:a4:bb:93:09:e2:72:
                    8e:d9:88:90:7d:b9:cc:81:bd:6a:76:f9:45:7c:7c:
                    65:a8:d3:57:7e:9b:a0:85:e8:fa:7a:43:03:97:a7:
                    60:65:1a:e2:54:d2:e5:42:54:37:4f:54:5d:6d:1d:
                    40:16:51:ed:76:58:79:8c:bd:2e:96:61:61:77:a2:
                    9d:72:3a:b1:8e:5c:ae:30:e6:68:cb:1f:9e:fe:7a:
                    48:dd:42:15:17:f4:80:68:0b:11:2f:80:3e:37:63:
                    a4:c2:98:ca:25:eb:b3:03:49:9a:9d:c7:07:ee:e1:
                    05:a1:05:a4:6b:e6:c8:87:5c:e5:4d:9f:33:43:ec:
                    47:10:44:36:d6:d1:6e:5d:f3:d8:78:d2:fb:e8:52:
                    3d:67:e5:f4:4b:62:6a:0e:cd:32:97:10:ee:89:54:
                    3f:5c:8e:44:2b:37:e7:2c:0d:41:42:e7:53:0d:aa:
                    6b:2b:ab:07:8e:08:83:f0:ab:de:d9:7a:5e:53:9a:
                    6a:2f:6c:2c:31:18:c1:a2:20:2a:c2:33:ad:9f:df:
                    42:45
                Exponent: 65537 (0x10001)
# more and more information...
```

これで公開鍵の準備はととのった。

# JWTの署名検証

すでに述べたように、JWTは`.`で3つBase64エンコードされたデータが連結されており、最後の部分が署名（またはメッセージ認証コード）である。今回のJWTにおいては`RS256`アルゴリズムが採用されているので、この部分はBase64エンコードされた署名データということになり、下記にそれを示した。

```
NiPnBsPrebR9GGGgJrfRUja4o34JxqV-HbE-uHGbd15kU0O6re7G8K4cfPJtoK0D2ns9oAusI8qGN7fhS0o9CfxLim3sHtB2ZWyy4t3Lkcj6rb0ixTdoNiKvhlozc2vBwOoq3lB-Rr4MieuJ30qYLO07Kl_910FqRw6hSrTlMyEP1G1ozBgljF_GesttJEOLhE975T3yPuqLVoYKMNEqCscQqZkb9J6W9nIxZracQFk1-99o4_SSKBUKqr8oeTg0xqjqTnvsJ3khvyzy70P3e3tOfyuV-nrFDBUuMPBk_F9scaJNDFuSGQzVhHaT4eOXsXxEJ3M6FX8Dj9dOK19ppg
```

これを`base64 -D`コマンドなどで戻しても表示が不可能なので、`hexdump`コマンドで見てみるとよい。また、Base64をデコードするときは適当に末尾に`=`を何個か付けないと成功しないことがある。

```console
$ echo "NiPnBsPrebR9GGGgJrfRUja4o34JxqV-HbE-uHGbd15kU0O6re7G8K4cfPJtoK0D2ns9oAusI8qGN7fhS0o9CfxLim3sHtB2ZWyy4t3Lkcj6rb0ixTdoNiKvhlozc2vBwOoq3lB-Rr4MieuJ30qYLO07Kl_910FqRw6hSrTlMyEP1G1ozBgljF_GesttJEOLhE975T3yPuqLVoYKMNEqCscQqZkb9J6W9nIxZracQFk1-99o4_SSKBUKqr8oeTg0xqjqTnvsJ3khvyzy70P3e3tOfyuV-nrFDBUuMPBk_F9scaJNDFuSGQzVhHaT4eOXsXxEJ3M6FX8Dj9dOK19ppg==" \
 | base64 -D | hexdump -C
00000000  36 23 e7 06 c3 eb 79 b4  7d 18 61 a0 26 b7 d1 52  |6#....y.}.a.&..R|
00000010  36 b8 a3 7e 09 c6 a5 7e  1d b1 3e b8 71 9b 77 5e  |6..~...~..>.q.w^|
00000020  64 53 43 ba ad ee c6 f0  ae 1c 7c f2 6d a0 ad 03  |dSC.......|.m...|
00000030  da 7b 3d a0 0b ac 23 ca  86 37 b7 e1 4b 4a 3d 09  |.{=...#..7..KJ=.|
00000040  fc 4b 8a 6d ec 1e d0 76  65 6c b2 e2 dd cb 91 c8  |.K.m...vel......|
00000050  fa ad bd 22 c5 37 68 36  22 af 86 5a 33 73 6b c1  |...".7h6"..Z3sk.|
00000060  c0 ea 2a de 50 7e 46 be  0c 89 eb 89 df 4a 98 2c  |..*.P~F......J.,|
00000070  ed 3b 2a 5f fd d7 41 6a  47 0e a1 4a b4 e5 33 21  |.;*_..AjG..J..3!|
00000080  0f d4 6d 68 cc 18 25 8c  5f c6 7a cb 6d 24 43 8b  |..mh..%._.z.m$C.|
00000090  84 4f 7b e5 3d f2 3e ea  8b 56 86 0a 30 d1 2a 0a  |.O{.=.>..V..0.*.|
000000a0  c7 10 a9 99 1b f4 9e 96  f6 72 31 66 b6 9c 40 59  |.........r1f..@Y|
000000b0  35 fb df 68 e3 f4 92 28  15 0a aa bf 28 79 38 34  |5..h...(....(y84|
000000c0  c6 a8 ea 4e 7b ec 27 79  21 bf 2c f2 ef 43 f7 7b  |...N{.'y!.,..C.{|
000000d0  7b 4e 7f 2b 95 fa 7a c5  0c 15 2e 30 f0 64 fc 5f  |{N.+..z....0.d._|
000000e0  6c 71 a2 4d 0c 5b 92 19  0c d5 84 76 93 e1 e3 97  |lq.M.[.....v....|
000000f0  b1 7c 44 27 73 3a 15 7f  03 8f d7 4e 2b 5f 69 a6  |.|D's:.....N+_i.|
00000100
```

内容を見てもよくわからないが、データが$10 \times 16 = 160$なので160byteであることが分かる。これをbitへ変換すると$160 \times 8 = 1280$となり1280bitである。このbit数は、たとえばSHA256なら256bitであるとか、RSAは公開鍵の情報からいって2048bitのようなよく知られたbit数に該当しないので、おそらくなんらかのバイナリフォーマットであろうということが分かる。とはいえこのバイナリフォーマットのパーズなどは全てOpenSSLに任せるので、いったんここでは放置して次のようなコマンドでこの署名データをバイナリデータとして保存する。

```console
$ echo "NiPnBsPrebR9GGGgJrfRUja4o34JxqV-HbE-uHGbd15kU0O6re7G8K4cfPJtoK0D2ns9oAusI8qGN7fhS0o9CfxLim3sHtB2ZWyy4t3Lkcj6rb0ixTdoNiKvhlozc2vBwOoq3lB-Rr4MieuJ30qYLO07Kl_910FqRw6hSrTlMyEP1G1ozBgljF_GesttJEOLhE975T3yPuqLVoYKMNEqCscQqZkb9J6W9nIxZracQFk1-99o4_SSKBUKqr8oeTg0xqjqTnvsJ3khvyzy70P3e3tOfyuV-nrFDBUuMPBk_F9scaJNDFuSGQzVhHaT4eOXsXxEJ3M6FX8Dj9dOK19ppg==" \
 | base64 -D > jwt.sign
```

そして次のOpenSSLコマンドで検証を実行する。

```console
$ openssl rsautl -verify -asn1parse -in jwt.sign -certin -inkey google_cert.pem
    0:d=0  hl=2 l=  49 cons: SEQUENCE
    2:d=1  hl=2 l=  13 cons:  SEQUENCE
    4:d=2  hl=2 l=   9 prim:   OBJECT            :sha256
   15:d=2  hl=2 l=   0 prim:   NULL
   17:d=1  hl=2 l=  32 prim:  OCTET STRING
      0000 - b2 a5 93 94 13 0c 31 8d-71 1a 13 0f b2 f2 2e 9f   ......1.q.......
      0010 - 1c 32 14 e5 23 6b 5e 3d-17 98 92 0a 09 e8 27 76   .2..#k^=......'v
```

最後の2行に出力されているハッシュ値のような16進数が全部で32byteある。$32 \times 8 = 256$なので256bitとなり、これはSHA256の出力結果であると思われる。あとはこのデータと、JWTにはいっているヘッダーとボディ部分のSHA256を比較すればよい。

```console
$ echo -n "eyJhbGciOiJSUzI1NiIsImtpZCI6IjFmODhiODE0MjljYzQ1MWEzMzVjMmY1Y2RiM2RmYjM0ZWIzYmJjN2YiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoi5ZCJ5p2R5YSqIiwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hLS9BT2gxNEdpWnp0M2o5ajRmNzRTYldqaTFMaHhmTWxOTzZlYXFyS2NnM2tSWkxRPXM5Ni1jIiwiaXNzIjoiaHR0cHM6Ly9zZWN1cmV0b2tlbi5nb29nbGUuY29tL2Zpci11aS1kZW1vLTg0YTZjIiwiYXVkIjoiZmlyLXVpLWRlbW8tODRhNmMiLCJhdXRoX3RpbWUiOjE1ODUwNjcyODIsInVzZXJfaWQiOiJlOFBjbXlKU0dmaEMwbGJIZDZSQWlFcG94MXYxIiwic3ViIjoiZThQY215SlNHZmhDMGxiSGQ2UkFpRXBveDF2MSIsImlhdCI6MTU4NTA2NzUxMSwiZXhwIjoxNTg1MDcxMTExLCJlbWFpbCI6Inl5dUBtZW50YWwucG9rZXIiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6eyJnb29nbGUuY29tIjpbIjEwMjEyMTUzOTY5Njc1NTExMDg0MyJdLCJlbWFpbCI6WyJ5eXVAbWVudGFsLnBva2VyIl19LCJzaWduX2luX3Byb3ZpZGVyIjoiZ29vZ2xlLmNvbSJ9fQ" \
 | shasum -a 256
b2a59394130c318d711a130fb2f22e9f1c3214e5236b5e3d1798920a09e82776  -
```

これが両方とも同じなのでOK :tada: となる。

# まとめ

このように手作業でもOpenSSLとBase64をデコードする`base64`コマンドさえあればJWTの署名を検証してみることができる。JWTは最近いろいろなところで見るようになったので、開発しているプログラムで検証失敗となったときにコマンドラインツールから追検証してみることができると便利だと思う。

