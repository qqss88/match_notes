import boto3
import os
import json

from boto3.s3.transfer import TransferConfig
from boto3.s3.transfer import S3Transfer

S3_ALLOWED_EXTENSIONS = {'bam', 'vcf', 'zip', 'bai', 'tsv'}


def aws_credentials():
    s3_conf = './resources/.s3_config.json'
    curr_dir = os.path.dirname(__file__)
    file_name = os.path.join(curr_dir, s3_conf)
    if not os.path.isfile(file_name):
        print 'aws config file missing.'
    with open(file_name) as config_file:
        config = json.load(config_file)
        if 'aws_access_key_id' not in config or 'aws_secret_access_key' not in config:
            print 'aws credentials not found.'
        return config['aws_access_key_id'], config['aws_secret_access_key']


def s3_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in S3_ALLOWED_EXTENSIONS


class S3Service(object):

    def __init__(self):
        self.__access_key, self.__secret_key = aws_credentials()

    def get_s3_connection(self):
        return boto3.resource('s3', aws_access_key_id=self.__access_key, aws_secret_access_key=self.__secret_key)

    def get_s3_transfer(self):
        # multipart_threshold=9999999999999999,  # workaround for 'disable' auto multipart upload
        my_config = TransferConfig(
            multipart_threshold=8000000,
            max_concurrency=10,
            num_download_attempts=10,
        )

        connection = boto3.client(service_name='s3',
                                  region_name='us-east-1',
                                  api_version=None,
                                  use_ssl=True,
                                  verify=True,
                                  aws_access_key_id=self.__access_key,
                                  aws_secret_access_key=self.__secret_key,
                                  aws_session_token=None,
                                  config=None)

        return S3Transfer(connection, my_config)

    def key_exists(self, bucket_name, key_name):
        s3 = self.get_s3_connection()
        bucket = s3.Bucket(bucket_name)
        objs = list(bucket.objects.filter(Prefix=key_name))
        return len(objs) > 0 and objs[0].key == key_name

    def bucket_exists(self, bucket_name):
        s3 = self.get_s3_connection()
        return s3.Bucket(bucket_name) in s3.buckets.all()
