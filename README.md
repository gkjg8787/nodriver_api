# nodriver_api

This project provides a FastAPI-based API to download the HTML content of a web page using `nodriver` and headless Chrome.

## Features

- Fetches HTML from a given URL.
- Waits for a specific CSS selector to appear or for a specified amount of time before retrieving the content.
- Manages a headless Chrome browser within a Docker container using `xvfb`.

## Requirements

- Docker

## How to Run

1.  **Build the Docker image:**

    ```bash
    docker build -t nodriver-api .
    ```

2.  **Run the Docker container:**

    The application runs on port 8090.

    ```bash
    docker run -p 8090:8090 --name nodriver-api-container nodriver-api
    ```

    *Note: Depending on the host system, you might need to add `--shm-size=2g` to the `docker run` command to provide enough shared memory for Chrome.*

## How to Test

You can send a POST request to the `/download` endpoint using `curl` or any other API client.

### Example Request

This example fetches the main page of Wikipedia after waiting for the element with the ID `#mp-topbanner` to be present.

```bash
curl -X POST http://localhost:8090/download \
-H "Content-Type: application/json" \
-d '{
  "url": "https://ja.wikipedia.org/wiki/%E3%83%A1%E3%82%A4%E3%83%B3%E3%83%9A%E3%83%BC%E3%82%B8",
  "wait_css_selector": "#mp-topbanner",
  "tag_wait_timeout": 10
}'
```

### API Payload (`DownloadRequest`)

-   `url` (string, required): The URL to download.
-   `page_load_timeout` (int, optional): Timeout for page loading in seconds.
-   `tag_wait_timeout` (int, optional): Timeout for waiting for the `wait_css_selector` in seconds.
-   `cookie_dict_list` (list[dict], optional): A list of cookie dictionaries to set in the browser.
-   `wait_css_selector` (str, optional): A CSS selector to wait for before getting the page content.
-   `page_wait_time` (float, optional): A fixed time to wait in seconds.
-   `pre_wait_time` (float, optional): A fixed time to wait in seconds *before* checking for `wait_css_selector`.

### API Response (`DownloadResponse`)

The API returns a JSON object with the following structure:

```json
{
  "result": "<html>...</html>",
  "error": {
    "error_msg": "",
    "error_type": ""
  }
}
```

-   `result`: The HTML content of the page as a string. Empty if an error occurs.
-   `error`: An object containing error details. Empty if the request is successful.
    -   `error_msg`: The error message.
    -   `error_type`: The type of the exception.