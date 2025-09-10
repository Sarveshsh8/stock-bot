#!/usr/bin/env python3

import boto3
import time
import sys

# Set up AWS client
eks_client = boto3.client(
    'eks',
    region_name='us-east-1',
    aws_access_key_id='AKIAUJRTKQNULWFWRMNV',
    aws_secret_access_key='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'
)

def create_cluster():
    print("Creating EKS cluster...")
    
    try:
        # Create cluster
        response = eks_client.create_cluster(
            name='stock-bot-cluster',
            version='1.29',
            roleArn='arn:aws:iam::295386645352:role/stock-bot-eks-cluster-role',
            resourcesVpcConfig={
                'subnetIds': [
                    'subnet-048e928af5238cf99',
                    'subnet-09f9d0ec25cd75d49',
                    'subnet-067cdf9014921c0d6',
                    'subnet-0b5323f3bdfb9dbf8'
                ]
            }
        )
        
        print("Cluster creation initiated!")
        print(f"Cluster ARN: {response['cluster']['arn']}")
        
        # Wait for cluster to be active
        print("Waiting for cluster to become active (this may take 10-15 minutes)...")
        waiter = eks_client.get_waiter('cluster_active')
        waiter.wait(name='stock-bot-cluster')
        
        print("Cluster is active!")
        
        # Create node group
        print(" Creating node group...")
        node_response = eks_client.create_nodegroup(
            clusterName='stock-bot-cluster',
            nodegroupName='stock-bot-nodes',
            nodeRole='arn:aws:iam::295386645352:role/stock-bot-eks-node-role',
            subnets=[
                'subnet-048e928af5238cf99',
                'subnet-09f9d0ec25cd75d49'
            ],
            instanceTypes=['t3.medium'],
            scalingConfig={
                'minSize': 1,
                'maxSize': 3,
                'desiredSize': 2
            }
        )
        
        print(" Node group creation initiated!")
        
        # Wait for node group to be active
        print("⏳ Waiting for node group to become active (this may take 5-10 minutes)...")
        node_waiter = eks_client.get_waiter('nodegroup_active')
        node_waiter.wait(clusterName='stock-bot-cluster', nodegroupName='stock-bot-nodes')
        
        print("EKS cluster and node group are ready!")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_cluster()
