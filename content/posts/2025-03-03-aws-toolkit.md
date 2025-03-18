+++
title = 'AWS Pentesting Toolkit: Practical Tools for Cloud Security Assessment'
date = 2024-04-15 09:30:22
draft = false
+++

> This suite of Python-based AWS security assessment tools demonstrates common techniques used during cloud penetration testing engagements. Through practical implementations of cross-account role assumption, credential extraction, S3 secret scanning, EC2 password enumeration, and credential exfiltration, security professionals can better understand the AWS attack surface. These tools highlight potential risk areas while providing a foundation for responsible cloud security testing within authorized environments.

## A Hodgepodge of AWS Hacking Tools

I've been poking around AWS environments for security assessments lately, and found myself writing the same code over and over again. So I finally took some time to package up a few of the scripts I use regularly into something a bit more reusable. Nothing fancy here - just some practical Python tools that make AWS pentesting a little easier.

Obviously, only use these in environments where you have permission to test. I'm not responsible for your career choices if you decide to point these at random AWS accounts.

## The Tools

### Assume Tool (assume_tool.py)

This is probably the one I use the most. When you're looking at AWS environments, jumping between accounts through IAM roles is one of the first things you need to figure out.

The tool does a few things:
- Can selectively target a list of roles and accounts
- For role brute-forcing, takes your best guesses about role names and tries them systematically
- Generates variations like "ServiceNameRole" or "AdminServiceRole"
- Tries to assume each role and tells you what works

It's surprisingly effective because most companies follow predictable naming patterns. I can't tell you how many times I've gotten into accounts by just trying `AdminRole` or `DevOpsExecutionRole`. You'd think security people would be more creative.

### S3 Credential Enumeration (s3_cred_enum.py)

This one scans S3 buckets looking for secrets and credentials. Almost all of the best low-hanging fruit I've seen have been in S3 buckets.

What it does:
- Looks through your accessible S3 buckets
- Scans files for things like AWS keys, API tokens, database passwords
- Shows you the context around matches so you can tell if they're real
- Skips binary files and other things you probably don't care about

S3 is like the junk drawer of the cloud - people toss everything in there and forget about it. Config files, backups, logs with credentials... I've found production database passwords sitting in buckets with public access. It's wild.

### EC2 Password Enumerator (enumerate_ec2_passwords.py)

A simple but handy script that:
- Lists all your EC2 instances
- Checks which Windows instances have password data available
- Shows you which ones you might be able to access

It doesn't actually decode the passwords (you'd need the right private key for that), but it tells you which instances are worth investigating further. Sometimes just knowing an instance has a retrievable password is enough to pivot your testing in a new direction.

### Lambda Credential Exfiltrator (lambda_to_aws_cred.py)

This is a Lambda function that pulls credentials from its own execution environment:
- Grabs the access key, secret key, and token
- Figures out what IAM role it's using
- Formats everything nicely as AWS credential file entries

It's a great demonstration of why you need to be careful about what code gets deployed to Lambda. If you can get your code running in someone's Lambda environment (through injection, dependency confusion, etc.), you can extract the credentials and potentially access all kinds of resources. You also need to be careful about who you give access to create, modify, and run Lambdas, because this straightforward way to access credentials can easily introduce lateral movement and privilege escalation opportunities.

### AWS Console Access Generator (get_aws_signon_url.py)

This script turns programmatic credentials into a clickable link for the AWS Console:
- Takes AWS credentials you've obtained
- Creates a federation token
- Builds a URL that instantly logs you into the console
- Even opens your browser for you

This one's great for demos. When you're showing a client how an attack path works, there's nothing quite like clicking a link and watching their AWS console appear without entering a password. Really drives home the impact of credential exposure.

## What These Tools Tell Us About AWS Security

Using these tools during pentests has taught me a few things:

1. **AWS IAM is complicated as hell.** Most security issues aren't from sophisticated attacks - they're from people not understanding the permission model.

2. **Cross-account access is rarely audited.** Companies set up trust relationships and then forget about them. I've seen prod accounts that trust dozens of dev accounts with minimal restrictions.

3. **S3 is a secret goldmine.** Everyone uses it, few people secure it properly. It's almost always worth scanning if you can get access.

4. **Credential management is still hard.** AWS has all these fancy tools, but people still hardcode secrets in Lambda functions and EC2 user data.

5. **The AWS console is too powerful.** Once you have console access, it's game over for most environments. The GUI makes it too easy to explore and pivot.

## Using These Responsibly

I shouldn't have to say this, but:

- Get written permission before testing
- Stay within scope
- Don't exfiltrate actual customer data
- Document what you do
- Clean up after yourself

AWS CloudTrail logs everything, so your activities will be recorded. Don't be the pentester who brings down prod or gets themselves reported to the authorities.

## Show Me the Code!

- https://gist.github.com/joshfinley/f2d5f8043dc18a3714429d33972e41ec
- https://gist.github.com/joshfinley/3fd96c6d008d92028066326c260d2fed
- https://gist.github.com/joshfinley/370f7ba2d9f905a686807e843c922eed
- https://gist.github.com/joshfinley/e01b79d1a820eb7be96d962a8f3fec22
- https://gist.github.com/joshfinley/5c93175c6627fec24f77fc42d0954c36

## Technical Bits Worth Noting

I built these with a few things in mind:

- They use boto3 efficiently, following AWS SDK best practices
- Error handling is decent - they won't crash if one API call fails
- They work with profiles, environment vars, or EC2 instance profiles
- Results are formatted for human readability (because I'm the human reading them)

None of this is rocket science - just practical tools for practical problems. Feel free to adapt them for your own needs.

## Wrap-Up

AWS security is a moving target, and these tools just scratch the surface of what's possible. The cloud gives us amazing capabilities, but it also creates complex security challenges that aren't always obvious.

The good news is that AWS provides pretty robust security controls. The bad news is that almost nobody uses them all correctly. As a pentester, that job security makes me happy. As someone who also uses cloud services, it keeps me up at night.

If you're responsible for AWS security, I'd recommend regularly testing your own environment with tools like these. You might be surprised what you find.

{{< footnote >}}I built these tools for legitimate security work. If you're wondering "can I use these to hack random AWS accounts?" - the answer is no, and also, please find a real career.{{< /footnote >}}
