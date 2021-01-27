# musabi

## EC2

Command to change cuda version on EC2

```sh
ls -l /usr/local/ | grep cuda
sudo rm /usr/local/cuda
sudo ln -s /usr/local/cuda-10.2 /usr/local/cuda
ls -l /usr/local/ | grep cuda
```
