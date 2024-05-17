import re
import os
import subprocess
import hashlib
import mimetypes
import requests

def calculate_sha256_from_file(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for block in iter(lambda: f.read(4096), b''):
            sha256.update(block)
    return sha256.hexdigest()

def archive_file(url, extension, content_type):
    tmp_archive_name = f"tmp{extension}"
    new_extension = extension
    if content_type == 'text/html':
        cmd = f'wkhtmltopdf "{url}" static/archives/{tmp_archive_name}.pdf'
        result = subprocess.run(cmd, shell=True)
        if result.returncode == 0:
            new_extension = '.pdf'  # Changing the extension to PDF as the output will be a PDF
        else:
            cmd = f'wget "{url}" -O static/archives/{tmp_archive_name}'
            subprocess.run(cmd, shell=True)  # Fallback to direct download
    elif extension == '.pdf':
        cmd = f'wget "{url}" -O static/archives/{tmp_archive_name}'
        subprocess.run(cmd, shell=True)
    elif extension in ['.jpg', '.png', '.jpeg', '.gif']:
        cmd = f'wget "{url}" -O static/archives/{tmp_archive_name}'
        subprocess.run(cmd, shell=True)
    else:
        print(f"Unsupported file type: {extension}. Skipping...")
        return None, extension

    return new_extension


def find_shortcode_references(content):
    return re.findall(r'{{< reference content="([^"]+)"', content)

def find_figure_shortcode_references(content):
    return re.findall(r'{{< figure src="([^"]+)"', content)

if not os.path.exists("static/archives/"):
    os.mkdir("static/archives/")

for filename in os.listdir("./content/posts"):
    if filename.endswith(".md"):
        filepath = f"./content/posts/{filename}"
        with open(filepath, 'r+') as f:
            content = f.read()

            references = find_shortcode_references(content)
            references = references + find_figure_shortcode_references(content)

            for ref in references:
                if ref.startswith("/archives/"):
                    continue
                if not ref.startswith("http://") and not ref.startswith("https://"):
                    continue
                url = ref.split('/')[-1]

               # Determine the file extension
                response = requests.get(ref)
                content_type = response.headers['content-type']
                extension = mimetypes.guess_extension(content_type)

                new_extension = archive_file(ref, extension, content_type)
                if new_extension is not None:
                    print(f"archived: {ref}")
                    # Calculate hash from the fetched content
                    hash_prefix = calculate_sha256_from_file(f"static/archives/tmp{new_extension}")

                    # Rename the file based on the hash
                    sanitized_url = url.split('//')[-1].replace('/', '_')

                    if sanitized_url.endswith(new_extension):
                        archive_name = f"{hash_prefix}_{sanitized_url}"
                    else:
                        archive_name = f"{hash_prefix}_{sanitized_url}{new_extension}"

                    os.rename(f"static/archives/tmp{new_extension}", f"static/archives/{archive_name}")

                    # Replace the URL in shortcode reference
                    new_ref = f"/archives/{archive_name}"
                    content = content.replace(ref, new_ref)
                    print(f"replaced url: {ref} -> {new_ref}")

            f.seek(0)
            f.write(content)
            f.truncate()
