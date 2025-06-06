# STEP6: テストを用いてAPIの挙動を確認する

このステップではテストに関する内容を学びます。

**:book: Reference**

* (JA)[テスト駆動開発](https://www.amazon.co.jp/dp/4274217884)
* (EN)[Test Driven Development: By Example](https://www.amazon.co.jp/dp/0321146530)

## テストとは
テストとは、システムやコンポーネントの挙動や性能を評価し、それらが仕様や要件を満たしているか確認するプロセスのことです。例えば、次のような `sayHello` というGoの関数について考えてみましょう。

```go
func sayHello(name string) string {
    return fmt.Sprintf("Hello, %s!", name)
}
```

この関数は見れば分かる通り、引数で渡される `name` 変数を用いて `Hello, ${name}!` のような文字列を組み立てる関数です。この関数は正しく振る舞うでしょうか？それを確認することが出来るのがテストです。

Goでは以下のようにテストを書くことが出来ます。詳しい書き方は後ほど記載するので、今は流し読みしてください。

```go
func TestSayHello(t *testing.T) {
    // Alice というテスト名でテストを実施
    t.Run("Alice", func(t *testing.T) {
        // 期待する返り値は Hello, Alice!
        want := "Hello, Alice!"

        // 引数は "Alice"
        arg := "Alice"
        // 実際に sayHello を呼び出す
        got := sayHello(arg)

        // 期待する返り値と実際に得た値が同じか確認
        if want != got {
            // 期待する返り値と実際に得た値が異なる場合は、エラーを表示
            t.Errorf("unexpected result of sayHello: want=%v, got=%v", want, got)
        }
    })
}
```

これを実行すると、下記の通り成功します。

```bash
=== RUN   TestSayHello
=== RUN   TestSayHello/Alice
--- PASS: TestSayHello (0.00s)
    --- PASS: TestSayHello/Alice (0.00s)
PASS
```

このようにして、関数などの機能をテストすることが出来ます。

## テストの目的
このテストには、下記のような目的があります。

- 欠陥の発見
- 要件の適合性の検証
- 性能評価
- 信頼性の評価
- セキュリティの評価
- ユーザビリティの評価
- 保守性の評価
など

特に、想定されている挙動をすることを保証してくれるのは大きなメリットです。例えば、今回のソースコードに、気づかないうちに変な文字列( `#` )を下記のように紛れ込ませてしまったとします。

```go
func sayHello(name string) string {
    return fmt.Sprintf("Hello, %s!#", name)
}
```

この時、目視では見落としてしまう可能性があります。しかし、テストを書いておくことで、このようなミスに気づくことが可能です。実際にテストを実行すると以下の通り失敗してエラーメッセージが表示されます。

```bash
=== RUN   TestSayHello
=== RUN   TestSayHello/Alice
    prog_test.go:20: unexpected result of sayHello: want=Hello, Alice!, got=Hello, Alice!#
--- FAIL: TestSayHello (0.00s)
    --- FAIL: TestSayHello/Alice (0.00s)
FAIL
```

このようにして、振る舞いをテストで保証することでソースコードの品質を担保することが出来ます。更に、複雑な機能を実装する際に、小さな機能ごとにテストを書きながら実装を進めることで、確実に動く部分を保証しながら開発を進めることが出来ます。これにより、想定外のバグが発生した時でも、原因となった箇所をある程度絞り込んで調査できるので、テストを書かないときと比較して迅速に対応することが可能です。

## テストの種類
このテストには用途に応じて様々な種類があります。

今回は簡単のために、上記のようなコンポーネントレベルで実施されるのが単体テスト(Unit Tests)、システム全体を統合した上で、ユーザの操作をシミュレーションしてテストするエンドツーエンドテスト(End-to-End Test/E2E Tests)の2種類を紹介します。興味のある方は各自で調べてください。

ここで、具体例に沿って考えてみましょう。例えば、画像投稿サイトで画像を投稿する機能のためのAPIの機能をテストする場合を想像してください。この場合、画像を投稿するAPIは、画像データを受け取って、結果を返却する関数/メソッドで実装されているはずです。そのため、想定される入力と出力を用いてテストすることが出来そうです。

しかし、テストのために毎回データベースを用意したり、サーバを起動したりするのは骨が折れます。そこで、画像をデータベースに保存する処理を実際に行わず、保存処理をするための関数/メソッドを、固定値を返す別の実装に置き換えてテストを行うことが出来ます。このような、テストのために固定値を返すようなものをモックと呼びます。

このようなモックを用いて、データベースに対する保存処理が失敗した時の挙動や成功した時の挙動を、実際にデータベースを用意せずに事細かに保証することが出来ます。しかし、このモックはあくまで僕らが勝手に指定した値なので、実際の挙動と異なるテストをしている可能性もあります。

このように、小さな機能のみのテストやモック等を用いた偽データを用いるテストを単体テスト(Unit Tests)と呼び、実際のデータベースやデータを用いて全体の機能をテストするテストをエンドツーエンドテスト(End-to-End tests: E2E tests)と呼びます。

基本的に単体テストの数がE2Eテストの数よりも多くなることが推奨されます。なぜなら、単体テストは高速かつ少ないリソースで実行することが出来ます。E2Eテストは遅く多くのリソースを必要とするためです。例えば、実データを利用するテストの場合、先ほどの例で考えると、テストデータを複数用意して、保存や削除を複数回行う必要があります。大規模データを扱う場合は実行時間が長くなったり利用リソースが増えたりするため、E2Eテストを少なめにして、単体テストで小さな機能を数でカバーするのが定石です。とはいえ、単体テストのみでは実際の環境固有で起きる問題に気付けなくなるという問題があるため、バランスが大事です。

## テスト戦略
テストの方針は言語、フレームワークによって異なります。本節では、GoとPythonにおけるテスト戦略について説明し、実際にテストを書く方法について説明します。

### Go

**:book: Reference**

- (EN)[testing package - testing - Go Packages](https://pkg.go.dev/testing)
- (EN)[Add a test - The Go Programming Language](https://go.dev/doc/tutorial/add-a-test)
- (EN)[Go Wiki: Go Test Comments - The Go Programming Language](https://go.dev/wiki/TestComments)
- (EN)[Go Wiki: TableDrivenTests - The Go Programming Language](https://go.dev/wiki/TableDrivenTests)

Goはテストに関連する機能を提供する `testing` と呼ばれる標準パッケージを有しており、 `$ go test` コマンドによってテストを行うことが可能です。Goが提示しているテストの方針については、[Go Wiki: Go Test Comments](https://go.dev/wiki/TestComments)を参照してください。言語としての一般的な方針が書かれています。これらの方針は必須という訳ではないので、問題のない範囲で倣うのが良いと思います。

では、実際に先ほどのコードの単体テストから書いてみましょう。Goではテストしたいケースを最初に列挙して、テーブルのように順番にテストするテーブルテスト(Table-Driven Test)を推奨しています。テストケースは基本的にスライスかmapで宣言することが多々ありますが、順序性が必要とされるケースでなければ、基本的にmapを利用すると良いと思います。実行順序に依存しないテストケースを書くことで、テスト対象の機能の振る舞いを、より強固に保証することが可能になるためです。

```go
func TestSayHello(t *testing.T) {
    cases := map[string]struct{
        name string
        want string
    }{
        "Alice": {
            name: "Alice",
            want: "Hello, Alice!"
        }
        "empty": {
            name: "",
            want: "Hello!"
        }
    }

    for name, tt := range cases {
        t.Run(name, func(t *testing.T) {
            got := sayHello(tt.name)

            // 期待する返り値と実際に得た値が同じか確認
            if tt.want != got {
                // 期待する返り値と実際に得た値が異なる場合は、エラーを表示
                t.Errorf("unexpected result of sayHello: want=%v, got=%v", tt.want, got)
            }
        })
    }
}
```

このように、テストケースをまとめて書くことで、一目で入力と想定される出力を確認することが出来ます。仮に、対象の関数/メソッドの振る舞いを全く知らないでコードリーディングする必要がある場合、テストコードを参考にして振る舞いを理解するヒントとして利用することもできます。

また、このようなテストも想定して、引数の設計を考えることも大事です。例えば、次のように、時間に応じて挨拶を変えるようにしたとします。

```go
func sayHello(name string) string {
    now := time.Now()
    currentHour := now.Hour()

    if 6 <= currentHour && currentHour < 10 {
        return fmt.Sprintf("Good morning, %s!", name)
    }
    if 10 <= currentHour && currentHour < 18 {
        return fmt.Sprintf("Hello, %s!", name)
    }
    return fmt.Sprintf("Good evening, %s!", name)
}
```

この場合、各時間帯の全てでテストをするためには、それぞれの時間にテストを実施しなければなりません。これはテスト的に適していない設計と言えます。テストできるようにするために、以下のように関数を書き換えることが出来ます。

```go
func sayHello(name string, now time.Time) string {
    currentHour := now.Hour()

    if 6 <= currentHour && currentHour < 10 {
        return fmt.Sprintf("Good morning, %s!", name)
    }
    if 10 <= currentHour && currentHour < 18 {
        return fmt.Sprintf("Hello, %s!", name)
    }
    return fmt.Sprintf("Good evening, %s!", name)
}
```

これにより、現在時刻を自由に設定できるようになったため、以下のように各時間帯の振る舞いをテストできるようになります。

```go
func TestSayHelloWithTime(t *testing.T) {
    type args struct {
        name string
        now time.Time
    }
    cases := map[string]struct{
        args
        want string
    }{
        "Morning Alice": {
            args: args{
                name: "Alice",
                now: time.Date(2024, 1, 1, 9, 0, 0, 0, time.UTC),
            },
            want: "Good morning, Alice!",
        },
        "Hello Bob": {
            args: args{
                name: "Bob",
                now: time.Date(2024, 1, 1, 12, 0, 0, 0, time.UTC),
            },
            want: "Hello, Bob!",
        },
        "Night Charie": {
            args: args{
                name: "Charie",
                now: time.Date(2024, 1, 1, 20, 0, 0, 0, time.UTC),
            },
            want: "Good evening, Charie!",
        },
    }

    for name, tt := range cases {
        t.Run(name, func(t *testing.T) {
            got := sayHello(tt.name, tt.now)

            // 期待する返り値と実際に得た値が同じか確認
            if tt.want != got {
                // 期待する返り値と実際に得た値が異なる場合は、エラーを表示
                t.Errorf("unexpected result of sayHello: want=%v, got=%v", tt.want, got)
            }
        })
    }
}
```

このようにして、テストのことも意識したコードをかけると良いですね。

## 1. 出品APIのテストを書く
基礎的な機能のテストである、アイテム登録のためのリクエストのテストを書いてみましょう。

想定されるリクエストは、 `name` および `category` を必要とするはずです。
そのため、そのデータが欠けている時にエラーを返すべきです。これをテストしてみましょう。

### Go
`server_test.go` を見てみましょう。

現在、AddItemのリクエストが来た時に全ての値が含まれている場合はOK、欠けている値がある場合はNGとしたいです。
そのようなテストケースを書いてみましょう。

**:beginner: Point**

- このテストは何を検証しているでしょうか？
- `t.Error()` と `t.Fatal()` には、どのような違いがあるでしょうか？

### Python
TBD

## 2. Hello Handlerのテストを書く
ハンドラのテストを書いてみましょう。

ハンドラのテストを書く際は、STEP 6-1と同様に、想定される値と引数を比較すれば良さそうです。

### Go

**:book: Reference**

- (EN)[httptest package - net/http/httptest - Go Packages](https://pkg.go.dev/net/http/httptest)
- (JA)[Goのtestを理解する - httptestサブパッケージ編 - My External Storage](https://budougumi0617.github.io/2020/05/29/go-testing-httptest/)

Goでは、 `httptest` と呼ばれるハンドラをテストするためのライブラリを用いてみましょう。

今回は、STEP6-1の時と異なり、比較する部分のコードが書かれていません。

- このハンドラでテストしたいのは何でしょうか？
- それが正しい振る舞いをしていることはどのようにして確認できるでしょうか？

ロジックが思いついたら実装してみましょう。

**:beginner: Point**

- 他の方が書いたテストコードを確認してみましょう
- httptestパッケージの既存コードで何をしているか確認してみましょう

### Python

TBD

## 3. モックを用いたテストを書く
モックを用いたテストを書いてみましょう。

モックは、先述の通り、実際のロジックを用いるのではなく、想定されたデータを返すような便利関数と実際の関数を置き換えるためのものです。このモックは様々な部分で利用できます。

例えば、今回のデータベースへのアイテム登録の部分を考えてみましょう。テストでは、データベースへのアイテム登録に成功する時と失敗する時を両方テストしたいはずです。しかし、これらのケースを意図的に引き起こすことは少々手間がかかります。また、実際のデータベースを利用すると、データベース側の問題でテストがflakyになる可能性もあります。

そこで、実際にデータベースのロジックを用いるのではなく、想定された返り値を返すようなモックを用いることで、あらゆるケースをテストすることが可能です。

### Go

**:book: Reference**

- (EN) [mock module - go.uber.org/mock - Go Packages](https://pkg.go.dev/go.uber.org/mock)

Goには様々なモックライブラリがありますが、今回は `gomock` を利用します。
`gomock` の簡単な利用方法はドキュメントや先駆者のブログを参照してください。

このモックを用いて、永続化の処理が成功するパターンと失敗するパターンの両方をテストしてみましょう。

**:beginner: Point**

- モックを満たすためにinterfaceを用いていますが、interfaceのメリットについて考えてみましょう
- モックを利用するメリットとデメリットについて考えてみましょう

### Python
TBD

## 4. 実際のデータベースを用いたテストを書く
STEP 6-3におけるモックを実際のデータベースに置き換えたテストを書いてみましょう。

モックは先述の通りあらゆるケースをテストすることが可能ですが、実際の環境で動かしている訳ではありません。そのため、実際のデータベース上では動かない、ということもしばしばあります。そこで、テスト用にデータベースを用意して、そのデータベースを利用してテストを実施しましょう。

### Go
Goでは、テスト用にデータベース用のファイルを作成して、そこに処理を足していく方針を取ります。

実際のデータベースで処理を行った後、データベース内のデータが想定通り変更されていることを確かめる必要があります。

- アイテム登録後のデータベースの状態はどうなっているはずでしょうか？
- それが正しい振る舞いをしていることはどのようにして確認できるでしょうか？

### Python
TBD

## Next

[STEP7: 仮想環境でアプリを動かす](./07-docker.ja.md)
