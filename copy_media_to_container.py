import os
import subprocess

LOCAL_MEDIA_PATH = os.path.join(os.getcwd(), 'media', 'gallery')
CONTAINER_NAME = 'django_app'
CONTAINER_MEDIA_PATH = '/app/media/gallery'

def copy_media():
    if not os.path.exists(LOCAL_MEDIA_PATH):
        print(f"Папка {LOCAL_MEDIA_PATH} не найдена.")
        return

    print("Копирую файлы в контейнер...")
    subprocess.run([
        'docker', 'exec', CONTAINER_NAME, 'mkdir', '-p', CONTAINER_MEDIA_PATH
    ])

    for filename in os.listdir(LOCAL_MEDIA_PATH):
        local_file = os.path.join(LOCAL_MEDIA_PATH, filename)
        if os.path.isfile(local_file):
            subprocess.run([
                'docker', 'cp', local_file,
                f"{CONTAINER_NAME}:{CONTAINER_MEDIA_PATH}/{filename}"
            ])
            print(f"Скопировано: {filename}")

if __name__ == '__main__':
    copy_media()