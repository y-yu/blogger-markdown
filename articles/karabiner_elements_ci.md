---
title: Karabiner-Elementsの設定JSONにCIを設定する
tags: Karabiner karabiner-Elements TravisCI
author: yyu
slide: false
---
# はじめに

[Karabiner-Elements](https://pqrs.org/osx/karabiner/)とはKarabinerの後継であり、macOSのキーバインド変更を行うためのアプリケーションである。特定のアプリケーションでのみ動作するキーバインドや、あるいは特定のキーと併用された場合にのみ動作をするといった複雑な設定を与えることができ、このような複雑な設定を_Complex modifications_と呼ぶ[^simple_modifictaions]。このComplex modificationsはJSON形式のファイルで管理することができ、GitHubとTravis CIを使うことでこのJSONに対してCIができる。この記事ではこのようなCIを構成する方法について解説する。
また、筆者が作成したものが下記のリポジトリーに置かれている。

- https://github.com/y-yu/karabiner-complex-modifications

[^simple_modifictaions]: Complex modificationsと対比して、「`a`を`b`にする」といったキーバインドのことを_Simple modifications_と言う。

# Karabiner CLI

実はKarabiner-ElementsにはCLIが同梱されており、下記のように使うことができる。

```console
$ "/Library/Application Support/org.pqrs/Karabiner-Elements/bin/karabiner_cli" --help
A command line utility of Karabiner-Elements.
Usage:
  karabiner_cli [OPTION...]

      --select-profile arg      Select a profile by name.
      --set-variables arg       Json string: {[key: string]: number}
      --copy-current-profile-to-system-default-profile
                                Copy the current profile to system default
                                profile.
      --remove-system-default-profile
                                Remove the system default profile.
      --lint-complex-modifications complex_modifications.json
                                Check complex_modifications.json
      --version                 Displays version.
      --version-number          Displays version_number.
      --help                    Print help.

Examples:
  karabiner_cli --select-profile 'Default profile'
  karabiner_cli --set-variables '{"cli_flag1":1, "cli_flag2":2}'
```

CIではこのCLIの`--lint-complex-modifications`オプションを利用する。

# Travis CIでの手順

GitHub上のリポジトリーにComplex modificationsのJSONファイルが設置されているとして、次のような方法で行う。

1. Travis CIのmacOS環境にhomebrew + caskでKarabiner-Elementsをインストール
2. Bashスクリプトを利用してフォルダー内のJSONを探索
3. `karabiner_cli`で（2）のJSONを検査

このような感じであり、具体的には次のような`.travis.yml`を用いた。

```yaml:.travis.yml
os: osx

osx_image: xcode11

language: generic

install:
  - brew cask install karabiner-elements

script:
  - ./test.sh
```

このあとで`test.sh`から`karabiner_cli`を起動して、それの終了コードを検査するだけである。

```bash:test.sh
#!/usr/bin/env bash

set -eo pipefail

SCRIPT_DIRECTORY="complex_modifications"

for FILENAME in `ls ./$SCRIPT_DIRECTORY`; do
  '/Library/Application Support/org.pqrs/Karabiner-Elements/bin/karabiner_cli' \
    --lint-complex-modifications \
    "${SCRIPT_DIRECTORY}/${FILENAME}"

  if [ $? != 0 ]; then
      exit 1
  fi
done
```

# まとめ（余談）

最初、Karabiner-ElementsのCIを作りたいと思ったときは`open`コマンドと`karabiner://`URLを利用するというのを考えていた。Karabiner-Elementsは`karabiner://`からインターネットやローカルにあるJSONファイルをインポートすることができるので、これでロードできたらOKというようなCIを作ろうとした。しかし、そのためにはどうしてもKarabinerのGUIを操作する必要があったので、次のようなAppleScriptを利用して強引に操作するという作戦を実行した。具体的には`open "karabiner://......"`を実行すると次のようなWindowが出現する。

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/c6b6086c-de8e-f31b-32ac-93bd572dd0f0.png)

注目してほしいのは、これがもしJSONに問題がある場合は`Import`ボタンが押せないことである。

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/dbe3c536-1d4b-3523-3fbf-856121562646.png)

これを利用して次のようなAppleScriptを用意した。これは（1）`Import`ボタンを押してみて、次に（2）`Cancel`ボタンを押してみる。もしここで（2）の`Cancel`ボタンを押すことに成功したということは、（1）で`Import`ボタンが押せなかったことを意味する。したがって（2）が成功したならば、JSONは壊れていると判断する。

```applescript
tell application "Karabiner-Elements" to activate

tell application "System Events"
	tell process "Karabiner-Elements"
		tell window "Karabiner-Elements Preferences"
			click button "Import" of sheet 1
			delay 1
			set result to ""
			try
				click button "Cancel" of sheet 1
			on error
				set result to "Success"
			end try
			
			if (result is not "Success") then
				error number -1
			end if
		end tell
	end tell
end tell
```

これをTravis CI上で実行したものの失敗に終った。今のmacOSは`System Events`といった何かしらのアプリケーションが、それとは違う別のアプリケーションを操作する場合は、アクセシビリティーのセキュリティをユーザーが許可しなければならない。かつてはこのセキュリティー権限を管理しているデータベースファイルを`sqlite3`コマンドで操作することができたらしいが、現在は絶対にGUIで操作しなければならない。もし自動でこの権限を操作できてしまうならば、マリシャスなアプリケーションはまず自動でセキュリティーを解除し、そのあとで他のアプリケーションを操作してしまうため、ここにGUIを求めるのはセキュリティー上の理由において正しいと思う。ともかくこういういった理由でこの作戦は失敗か、あるいはTravis CIの中の人にお願いしてApple Scriptのインタープリターにあらかじめセキュリティー許可を与えてもらうといった方法をとるしかなく、かなり途方に暮れていた。そのあとでもう一度調べなおしてみたところ参考文献の情報に出会い、この記事の方法でCIができることとなった。

# 参考文献

- [Is there a JSON schema for Karabiner configs? (GitHub Issue of Karabiner-Elements)](https://github.com/tekezo/Karabiner-Elements/issues/1918#issuecomment-532486977)
- [Import file from another site (Karabiner-Elements README.md)](https://github.com/pqrs-org/KE-complex_modifications/#import-file-from-another-site)

この他にもAppleScript関連のサイトをいくつか読んだはずだが、どれを読んだのかもう分からなくなってしまった…… :innocent: 

