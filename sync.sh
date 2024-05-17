hugo -D
aws s3 sync ./public s3://fielyn.net --profile fielyn
