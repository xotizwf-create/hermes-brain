# One-off: upload the locally built Albery frontend dist to prod (186) via SFTP.
# Extract + atomic swap happen in a separate _deploy_helper command afterwards.
import sys

sys.path.insert(0, r"G:\OneDrive\Рабочий стол\Мои проекты\Сайт мой")
import _deploy_helper  # noqa: E402

client = _deploy_helper.connect("prod")
sftp = client.open_sftp()
sftp.put(r"C:\Users\hotiz\AppData\Local\Temp\albery_dist.tar.gz", "/tmp/albery_dist.tar.gz")
sftp.close()
client.close()
print("uploaded")
