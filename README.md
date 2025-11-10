# 概要

nodriver+chrome+Xvfb を使用してサイトの HTML のダウンロードをする API

# API

POST /download

## Request Body

```json
{
  "url": "string",
  "cookie": {
    "cookie_dict_list": [
      {
        "name": "string",
        "value": "string",
        "domain": "string",
        "path": "string"
      }
    ],
    "return_cookies": false,
    "save": false,
    "load": false,
    "filename": "string"
  },
  "wait_css_selector": {
    "selector": "css_selector",
    "timeout": 10,
    "on_error": {
      "action_type": "string",
      "max_retries": 0,
      "wait_time": 0.0,
      "check_exist_tag": "css_selector"
    },
    "pre_wait_time": 0.0
  },
  "page_wait_time": 0.0
}
```

| key                                        | require | description                                         |
| ------------------------------------------ | ------- | --------------------------------------------------- |
| url                                        | yes     | html 取得対象                                       |
| cookie                                     | no      | cookie 設定                                         |
| cookie.cookie_dict_list                    | no      | "name", "value", "domain"をキーに持つ dict の list  |
| cookie.return_cookies                      | no      | True の場合、response に cookie を返却              |
| cookie.save                                | no      | True の場合、cookie をファイルに保存 default: false |
| cookie.load                                | no      | True の場合、cookie をファイルから読み込み default: false |
| cookie.filename                            | no      | cookie の保存/読み込みに使用するファイル名。指定しない場合はドメイン名から自動生成 |
| wait_css_selector                          | no      | css selector 設定                                   |
| wait_css_selector.selector                 | yes     | ページ取得前に待つ対象の css selector               |
| wait_css_selector.timeout                  | no      | selector を待つ時間(sec) default: 10                |
| wait_css_selector.on_error                 | no      | selector が見つからなかった場合のエラーハンドリング |
| wait_css_selector.on_error.action_type     | no      | "raise" or "retry" default: "raise"                 |
| wait_css_selector.on_error.max_retries     | no      | retry 回数 default: 0                               |
| wait_css_selector.on_error.wait_time       | no      | retry 前の待ち時間(sec) default: 0.0                |
| wait_css_selector.on_error.check_exist_tag | no      | retry 前に存在する事を確認する css selector         |
| wait_css_selector.pre_wait_time            | no      | selector を待つ前に待つ時間(sec) default: 0.0       |
| page_wait_time                             | no      | ページ取得前に待つ時間(sec)                         |

## Response Body

```json
{
  "result": "string",
  "cookies": [],
  "error": {
    "error_msg": "",
    "error_type": ""
  }
}
```

| key     | type       | description |
| ------- | ---------- | ----------- |
| result  | string     | html        |
| cookies | list[dict] | cookie      |
| error   | dict       | エラー内容  |

# 注意事項

- 複数のリクエストを同時に受けるようには作ってない。
- javascript で動くサイトの取得の場合は事前に調整(css_selector)が必要。
- 現状、docker だと xvfb のロックファイルが残ってしまっているので fastapi を立ち上げる際に削除している。

# 使い方

## build

```
docker build -t nodriver-api .
```

## run

```
docker run --init -p 8090:8090 --name nodriver-api-container nodriver-api
```

## test

```
curl -X POST http://localhost:8090/download \
-H "Content-Type: application/json" \
-d '{
  "url": "https://ja.wikipedia.org/wiki/%E3%83%A1%E3%82%A4%E3%83%B3%E3%83%9A%E3%83%BC%E3%82%B8",
  "wait_css_selector": {
        "selector":"#welcome",
        "timeout":10,
        "on_error": {
            "action_type": "retry",
            "max_retries": 1
        },
        "pre_wait_time":0.5
    }
}'
```
