---
title: SwaggerのYAML/JSONをアノテーションから作るsbtプラグインを作った
tags: Scala sbt swagger
author: yyu
slide: false
---
# はじめに

[Swagger](https://swagger.io/)はAPIドキュメントやモック、クライアントなどを様々なプログラム言語で作成できるツールである。API情報は特定のフォーマットに従うYAML/JSONファイルで与えることができる。ScalaやJavaのようなプログラム言語において、APIの情報はコントローラーの実装部分にアノテーションを付与することがあり、Swaggerもアノテーションを解釈してYAML/JSONを出力する機能がある。これを利用したsbtプラグインはいくつか作られているが、それらが筆者の要求する機能を持たなかったので新しいsbtプラグイン[sbt-swagger-meta](https://github.com/y-yu/sbt-swagger-meta)を作成することとした。この記事ではSwaggerのAPI情報を記述するYAML/JSONを自作する際に苦労した点などについて述べる。なおこのプラグインは次のリポジトリで公開されている。

- https://github.com/y-yu/sbt-swagger-meta

# 既存のsbtプラグインの問題

アノテーションからSwaggerのファイルを作成するプラグインとしては次のようなものがある。

- [sbt-swagger](https://github.com/hootsuite/sbt-swagger)
- [sbt-swagger-2](https://github.com/scalalandio/sbt-swagger-2)

これらの問題は次のようなものがある。

<dl>
  <dt>YAMLファイルの出力ができない</dt>
  <dd>筆者はJSONだけではなく、YAMLも出力したいと考えていた。しかしこれらのプラグインはJSONを出力する機構しか持たない。</dd>

  <dt>sbt1.0とsbt0.13の両方で使いたい</dt>
  <dd>筆者の用途ではsbt1.0とsbt0.13の両方で動かしたいという要求があったが、どちらかにしか対応していない。</dd>

  <dt>更新が止っている</dt>
  <dd>最終更新が古いので、利用することが躊躇われる。</dd>
</dl>

これらの理由により新しいsbtプラグインを作成することした。

# sbt-swagger-metaの使い方

たとえば次のようなScalaファイルがあるとする。

```scala:UserEndpoints.scala
import io.swagger.annotations._
import javax.ws.rs._
import scala.annotation.meta.field

@Path("/users") @Api(value = "/users")
@Produces(Array("application/json"))
object UserEndpoints {
  @GET @Path("")
  @ApiOperation(value = "Get the key with the supplied key ID.")
  @Produces(Array("application/json"))
  @ApiResponses(Array(
    new ApiResponse(code = 200, message =
      "Success. Body contains key and creator information.",
      response = classOf[Response.User]
    ),
    new ApiResponse(code = 400, message =
      "Bad Request. Errors specify: (snip)",
      response = classOf[Response.BadRequest]),
    new ApiResponse(code = 404, message = "Not Found.",
      response = classOf[Response.NotFound])))
  def getByEmail(email: String): Response.User = ???
}

sealed trait Response
object Response {
  case class User(
    @(ApiModelProperty @field)(value = "email address") email: String
  ) extends Response

  case class BadRequest(
    @(ApiModelProperty @field)(value = "error message") msg: String
  ) extends Response

  case class NotFound(
    @(ApiModelProperty @field)(value = "error message") msg: String
  ) extends Response
}
```

- https://github.com/y-yu/sbt-swagger-meta/blob/4dddad35308bd64bef3e0c713726dff6b4885b5d/example/src/main/scala/UserEndpoints.scala

このファイルから次のようなYAMLが得られる。

```yaml
---
swagger: "2.0"
info:
  description: ""
  version: "2.0"
  title: "API docs"
tags:
- name: "users"
paths:
  /users:
    get:
      tags:
      - "users"
      summary: "Get the key with the supplied key ID."
      description: ""
      operationId: "getByEmail_1"
      produces:
      - "application/json"
      parameters:
      - in: "body"
        name: "body"
        required: false
        schema:
          type: "string"
      responses:
        200:
          description: "Success. Body contains key and creator information."
          schema:
            $ref: "#/definitions/User"
        400:
          description: "Bad Request. Errors specify: (snip)"
          schema:
            $ref: "#/definitions/BadRequest"
        404:
          description: "Not Found."
          schema:
            $ref: "#/definitions/NotFound"
definitions:
  User:
    type: "object"
    properties:
      email:
        type: "string"
        description: "email address"
  BadRequest:
    type: "object"
    properties:
      msg:
        type: "string"
        description: "error message"
  NotFound:
    type: "object"
    properties:
      msg:
        type: "string"
        description: "error message"
```

# sbt-swagger-metaの作成で苦労したところ

それでは実際にsbt-swagger-metaを作るにあたって苦労したところをいくつか述べる。

## アノテーションを変更してからYAML/JSONファイルを再生成しても変化しない

これは当初、次の方法で`PluginClassLoader`を得ていた。

```scala:Sbt.scala
val pluginClassLoader = classOf[com.wordnik.swagger.annotations.Api].getClassLoader.asInstanceOf[PluginClassLoader]
```

- https://github.com/hootsuite/sbt-swagger/blob/6ddb3e39f5548824d02bee5fcf9794ebc81041ad/src/main/scala/com/hootsuite/sbt/swagger/Sbt.scala#L58

ところが、`PluginClassLoader`はシングルトンであるためクラスローダーが変化せずアノテーションを変更してもsbtを再起動しない限り生成される`swagger.json`などが変更されない。そこで、[@xuwei-k](https://twitter.com/xuwei-k)さんの[sbt の Task で、メインの任意のメソッドを実行してその結果を取得する](https://xuwei-k.hatenablog.com/entry/20130310/1362897747)を参考に次のような方法でクラスローダーを作成するようにした。

```scala:SbtSwaggerMeta.scala
val mainClassLoader = Internal.makeLoader(fullClasspath.map(_.data), classOf[Api].getClassLoader, scalaInstanceInCompile)
val pluginClassLoader = Internal.makePluginClassLoader(mainClassLoader)

pluginClassLoader.add(fullClasspath.files.map(_.toURI.toURL))
```

なお、`Internal`はsbt1.0とsbt0.13で`ClasspathUtilities`などのパスが変更されているため、その差を吸収するために次のように作成した。

```scala:sbt-1.0/Internal.scala
private[sbtswaggermeta] object Internal {
  def makeLoader(classpath: Seq[File], parent: ClassLoader, instance: ScalaInstance): ClassLoader
    = internal.inc.classpath.ClasspathUtilities.makeLoader(classpath, parent, instance)

  def makePluginClassLoader(classLoader: ClassLoader): PluginClassLoader = new PluginClassLoader(classLoader)
}
```

```scala:sbt-0.13/Internal.scala
private[sbtswaggermeta] object Internal {
  def makeLoader(classpath: Seq[File], parent: ClassLoader, instance: ScalaInstance): ClassLoader
    = sbt.classpath.ClasspathUtilities.makeLoader(classpath, parent, instance)

  def makePluginClassLoader(classLoader: ClassLoader): PluginClassLoader = new PluginClassLoader(classLoader)
}
```

## swagger-scala-moduleを利用してもYAMLの生成が変になる

[swagger-scala-module](https://github.com/swagger-api/swagger-scala-module)はJavaで作られたSwaggerにScalaの`Option`や`Either`といった型のシリアライズ方法を教えるパッケージであるが、これがYAMLを出力するときに機能しなかった。調べると次のようにJSONの場合のみに変更していた。

```scala:SwaggerScalaModelConverter.scala
object SwaggerScalaModelConverter {
  Json.mapper().registerModule(new DefaultScalaModule())
}
```

- https://github.com/swagger-api/swagger-scala-module/blob/0857176e44d6ce92cc31f11b247ee3df48cc18d7/src/main/scala/io/swagger/scala/converter/SwaggerScalaModelConverter.scala#L14-L16

そこで、やや強引だが次のようにYAMLにも反映させた。

```scala:SwaggerScalaModelConverterWithYaml.scala
class SwaggerScalaModelConverterWithYaml extends SwaggerScalaModelConverter

object SwaggerScalaModelConverterWithYaml {
  def apply: SwaggerScalaModelConverterWithYaml = {
    Yaml.mapper().registerModule(DefaultScalaModule)
    new SwaggerScalaModelConverterWithYaml()
  }
}
```

## exampleでsbtプラグインを利用する

sbt-swagger-metaはプラグイン本体と、`example`というフォルダにこのプラグインの利用例が入っている。このexampleでsbt-swagger-metaを利用するため、最初は`sbt publishLocal`して利用していたが、[@xuwei-k](https://twitter.com/xuwei-k)さんの記事[sbt plugin作成時のデバック、テスト方法](https://xuwei-k.hatenablog.com/entry/20120920/1348168081)では`sbt publishLocal`するのではない方法があった。ところが、これをやってみても上手く動作しない。しばらくネットの海を調べたところ、何かのプラグインで`example/project/plugins.sbt`に次のような記述をして解決していた。

```scala:example/project/plugins.sbt
lazy val root = Project("plugins", file(".")) dependsOn sbtSwaggerMeta

lazy val sbtSwaggerMeta = ClasspathDependency(RootProject(file("..").getAbsoluteFile.toURI), None)
```

- https://github.com/y-yu/sbt-swagger-meta/blob/3468fcedc84d25e1da8e83abf183d352d7ba3d51/example/project/plugins.sbt

これにより、`version.sbt`と`example/plugins.sbt`でバージョンを二重に管理しなくてもよくなったうえ、`sbt publishLocal`していたときはexample側のsbtを再起動しなければならないときがしばしばあったが、それもなくなり一石二鳥であった。

## Sonatypeへパブリッシュする際のGPG鍵に空のパスフレーズを利用する

Sonatypeへパブリッシュする際には署名が必要であり、[sbt-pgp](https://github.com/sbt/sbt-pgp)を利用すればこの作業を簡単に行うことができる。ところがsbt-pgpで鍵を作る際には空のパスフレーズで特に何も警告されないが、いざ[sbt-release](https://github.com/sbt/sbt-release)を利用していざリリースをするときに次のように表示されて空のパスフレーズが入力できない。

```console
Please enter PGP passphrase (or ENTER to abort):
```

秘密鍵のパスフレーズを渡す手段として、sbt-pgpの[ドキュメント](https://www.scala-sbt.org/sbt-pgp/usage.html)によれば`~/.sbt/pgp.credentials`というファイルを利用する方法が書かれていたが、これに空のパスフレーズを入れたものの上手くいかなかった。このため、筆者は次のようなファイル`pgp.sbt`を利用して次のようにした。

```scala:pgp.sbt
pgpPassphrase := Some(Array())
```

もし秘密鍵にパスフレーズを設定していないことを明かにしたくない場合は、Gitの機能で`pgp.sbt`が見えないようにしておくといいだろう[^unstage]。

[^unstage]: ただし、`sbt release`するときにUnstagedなファイルがあると処理が中断されてしまうので、何かよい手を考える必要がある。

# まとめ

これを利用してSwaggerのドキュメントをアノテーションから容易に得られるようになった。もうちょっと使ってみて、なにか追加するべき機能があればひきつづき実装していきたい。また、このプラグインを[Sonatype](https://search.maven.org/)へパブリッシュする際には次の文章を参考にした。

- [自作のScalaライブラリをMaven Central Repositoryにリリースする](https://qiita.com/kiris/items/b043a7582c22110d7097)

