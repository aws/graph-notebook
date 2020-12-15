## Connecting a local graph-notebook to Amazon Neptune (first-time setup)
When using graph-notebook locally to connect to an Amazon Neptune database for the first time, there are a couple of additional steps. This section assumes that you've already installed & configured [graph-notebook](https://github.com/aws/graph-notebook#installation) locally.  Please note that this wiki is not an official recommendation on network setups as there are many ways to connect to Amazon Neptune from outside of the VPC, such as setting up a load balancer or VPC peering.

Amazon Neptune DB clusters can only be created in an Amazon Virtual Private Cloud (VPC).  One way to connect to Amazon Neptune from outside of the VPC is to set up an Amazon EC2 instance as a proxy server within the same VPC. With this approach, you will also want to set up an SSH tunnel to securely forward traffic to the VPC. 

### Part 1: Set up a EC2 proxy server.
Launch an [Amazon EC2](https://aws.amazon.com/ec2/) instance located in the same region as your Neptune cluster. In terms of configuration, a standard Amazon Linux AMI can be used.  Since this is a proxy server, you can choose the lowest resource settings.  

Make sure the EC2 instance is in the same VPC group as your Neptune cluster. To find the VPC group for your Neptune cluster, check the console under [Neptune](https://console.aws.amazon.com/neptune/home) > Subnet groups. The instance's security group needs to be able to send and receive on port 22 for SSH and port 8182 for Neptune.  See below for an example security group setup.  

![Sample EC2 Inbound Rules](/././images/sample-ec2rules.png)

Lastly, make sure you save the key-pair file (.pem) and note the directory for use in the next step.

### Part 2: Set up an SSH tunnel.
This step can vary depending on if you are running <b>Windows</b> or <b>Mac</b>.

1. Modify your hosts file to map localhost to your Neptune endpoint. 

    <b>Windows: </b> Open the hosts file as an Administrator (C:\Windows\System32\drivers\etc\hosts)

    <b>MacOS: </b> Open Terminal and type in the command: `sudo nano /etc/hosts`

    Then add the following line to the hosts file.
    `127.0.0.1   localhost   your-Neptune-endpoint-here`

2. Open Command Prompt as an Administrator (or Terminal for MacOS) and navigate to the directory where you saved the EC2 key-pair file.  Run the following command:

    `ssh -i path/to/keypairfilename.pem ec2-user@yourec2instanceendpoint -N -L 8182:yourneptuneendpoint:8182`


    The -N flag will log you in instead of prompting for the information already included as part of your command when logging into EC2. An initial successful connection will ask you if you want to continue connecting? Type yes and enter.  

    To test the success of your local graph-notebook connection to Amazon Neptune, open a browser and navigate to:

    `https://yourneptunendpoint:8182/status` 

    You should see a report, similar to the one below, indicating the status and details of your specific cluster:

```
{
  "status": "healthy",
  "startTime": "Wed Nov 04 23:24:44 UTC 2020",
  "dbEngineVersion": "1.0.3.0.R1",
  "role": "writer",
  "gremlin": {
    "version": "tinkerpop-3.4.3"
  },
  "sparql": {
    "version": "sparql-1.1"
  },
  "labMode": {
    "ObjectIndex": "disabled",
    "DFEQueryEngine": "disabled",
    "ReadWriteConflictDetection": "enabled"
  }
}
```

Now, you should be able to run queries from your local Jupyter graph notebook to your Neptune clusters!  When you're ready to close the connection, use Ctrl+D to exit.

### Troubleshooting

If you're having trouble with seeing a successful status to Neptune, try the following:

<b>EC2 login: </b> make sure your key-pair (.pem) file is valid.  Use a basic form of the ssh command to see if you can login to EC2.
`ssh -i path/to/keypairfilename.pem ec2-user@yourec2instanceendpoint` 

A successful login with the above command will show a login confirmation like the one below:
```
Last login: Tue Dec 15 21:22:56 2020 from X.X.X.X

       __|  __|_  )
       _|  (     /   Amazon Linux 2 AMI
      ___|\___|___|

https://aws.amazon.com/amazon-linux-2/
```
<b>DNS flush: </b> after setting your hosts file, do a DNS flush to make sure your changes are reflected in the DNS.

<b> HTTPS: </b> Check that when you connect to Neptune via a browser that you're using `https://` in the URL.
