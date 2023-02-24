# Decrypting Cisco UCS backups
During a penetration test I came across backup files from UCS Manager that had an encryption scheme for the passwords
that I hadn't seen before:
```xml
<commSnmpUser auth="sha" descr="" name="snmp-user" 
    privpwd="SwfZz8P8VM2i6hiJWn9A7A==" 
    pwd="SwfZz8P8VM2i6hiJWn9A7A==" 
    useAes="yes"/>
```
Searching the internet didn't yield any positive results, so I started digging into the crypto.  This turned out to be 
simple XOR with a hardcoded key. The file had multiple passwords like this, and one of them was the password
to the FTP server where UCS uploads the backup I found. Since I had that password, I could start decrypting part of the key. Using 
known plaintext attacks, I've been able to extract 120 bytes of the key. I know the key is even longer, but this
is more than enough to decode all passwords in the config backup:

I don't know why the admin portal say "Auth type: SHA" and "Use AES-128: Yes" when creating this user, but it can't be about how the passwords are stored.

```
./cisco-ucs-decrypt.py "SwfZz8P8VM2i6hiJWn9A7A=="
ButYouSaidAES128
```

SNMP community name, TACACS passwords etc are all encrypted with this static key. The key is the same across all UCS servers I've seen - including a sample found on github: https://github.com/dcv-cloud/content-hx

Getting local access to UCS Manager from the configuration backup is interesting enough, but UCS also saves passwords used to
mount file shares:
```xml
<cimcvmediaConfigMountEntry authOption="default" description="" deviceType="cdd" 
    imageFileName="VMware-VMvisor-Installer-6.7.0.iso" imageNameVariable="none" 
    imagePath="\\fileserver\vSphere\" mappingName="67-update2" mountProtocol="cifs" 
    password="WxfM+sDwJ8mq/SDsfSFSpOFSn+iYwI8iIySto9W1FJrmKvbddg==" 
    userId="admin" writable="no"/>
```

A stored admin password to a file share can make it easier to perform lateral movement.

The passwords of local users doesn't need to be decrypted for clear-text reuse, so they are slightly better protected:
```xml
<aaaUser accountStatus="active" clearPwdHistory="no" descr="" email="no@no.no" 
    encPwd="LUOJzsG/KJmHuTfoeQAlpPxPgP3V86wfOnWQpMqSQ5j9cA==" 
    encPwdSet="no" 
    expiration="2022-06-29T22:00:00.000" name="oddrune" phone="" pwd="">
```

This encPwd decrypts to what Cisco calls "type 5", a salted MD5 hash:
```
./cisco-ucs-decrypt.py "LUOJzsG/KJmHuTfoeQAlpPxPgP3V86wfOnWQpMqSQ5j9cA=="
$1$Xm6/5L7n$pNWptkpamDJIqqIovTwqo/
```
While it's better than plain text, it's not very hard to brute force. The MD5 algorithm is not [NIST approved](https://media.defense.gov/2022/Feb/17/2002940795/-1/-1/0/CSI_CISCO_PASSWORD_TYPES_BEST_PRACTICES_20220217.PDF). 

## Obfuscation?!
The password for the LDAP provider is a very interesting case:
```xml
<aaaLdapProvider attribute="kek" basedn="kek" descr="" enableSSL="no" 
    encKey="XxPK7MbgaMiH5Tu4Yi0ekfJOn+bV1p8jag==" 
    filter="" key="" name="dummy" order="1" port="389" 
    retries="1" rootdn="kek" timeout="30" vendor="OpenLdap">
```

Decoding this resulted in unexpected clear text: "VagzjiodLkbtkclEzjozmayu!"

This is not the password I expected, but this text has capital letters and exclamation mark in the same place as the actual password, so I suspected a substitution cipher. Knowing Cisco has a history of using Vigenère ciphers for their legacy (type 7) passwords, I explored that path and was able to extract a working key: "DWEFSAVFSDKFQWEQYRMFVSFWTH". 

```
./cisco-ucs-vigenere.py VagzjiodLkbtkclEzjozmayu!
SecurityThroughObscurity!
```
Not sure why this last step was added to some passwords, but I guess two hardcoded keys is better than one?

## There is more
The configuration backup I found was accompanied by a tar-file that unpacked to a set of files that seems to be encrypted
with the same XOR-key, but a longer key than what I have been able to extract so far.
```
~/ucs/fullstate ❯❯❯ ls -l
total 4360
-rw-r--r--  1 m90175  staff       25 May 24 21:42 DB.ENCRYPT
-rw-r--r--  1 m90175  staff    51200 May 24 21:43 certstore.tar.data
drwxr-xr-x  2 m90175  staff       64 May 24 21:42 connector
-rw-r--r--  1 m90175  staff  2170014 May 24 21:43 dme.db.gz.crypt
-rw-r--r--  1 m90175  staff      513 May 24 21:43 sam.config.data
```

The sam.config.data file is promising, since it seems to be a INI file of a predictable format, but I haven't tried any further decrypting.


# Disclosure
Cisco was notified 2022-05-30, and nine months later [CVE-2023-20016](https://sec.cloudapps.cisco.com/security/center/content/CiscoSecurityAdvisory/cisco-sa-ucsm-bkpsky-H8FCQgsA) was born.
