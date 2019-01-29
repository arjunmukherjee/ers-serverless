## Keeping lambda functions warm
[Lambda Pricing](https://aws.amazon.com/lambda/pricing/)

- Define a function in a helper module (?)
- 
    ```
        def check_if_warmup_and_return(event, log):
        try:
            if event['source'] == 'serverless-plugin-warmup':
                log.info('WarmUP - Lambda is warm!')
                response = {"statusCode": 200}
                return response
        except:
            # Not a call from the warmup plugin
            return
    ```
- Add this as the first few lines to every function you wish to keep warm
- 
    ```
        response = check_if_warmup_and_return(event, log)
        if response is not None:
            return response
    ``` 
- `npm install serverless-plugin-warmup --save-dev`
- Under `plugins` in `serverless.yml` add another list item `serverless-plugin-warmup`
- For each function in `config/functions.yml` add `warmup: false`, setting the value to `true/false` as desired
    