import cloudinary
import cloudinary.uploader
import logging
from django.conf import settings

cloudinary.config(**settings.CLOUDINARY)
logger = logging.getLogger(__name__)

# def upload_audio(file):
    # try:
        
    #     if hasattr(file, 'seekable') and file.seekable():
    #         file.seek(0)
            
            
    #     result = cloudinary.uploader.upload(
    #         file,
    #         resource_type="auto",
    #         folder=settings.CLOUDINARY['folder'],  # Ensure folder is set if needed
    #         allowed_formats=["wav", "mp3", "webm"],
    #         overwrite=True,
    #         use_filename=True,
    #         unique_filename=False,
    #         timeout=30
    #     )
    #     logger.info(f"Cloudinary upload result: {result}")
    #     return {
    #         'public_id': result['public_id'],
    #         'url': result['secure_url'],
    #         'duration': result.get('duration', 0)
    #     }
    # except Exception as e:
    #     logger.error(f"Cloudinary error: {str(e)}")
    #     raise Exception(f"Cloudinary upload failed: {str(e)}")
# cloudinary.py update
# def upload_audio(file):
#     try:
#         result = cloudinary.uploader.upload(
#             file,
#             resource_type="auto",  # Auto-detect audio
#             folder='audio_interview',
#             # allowed_formats=["wav", "mp3", "ogg"],
#             timeout=60
#         )
#         return {
#             'public_id': result['public_id'],
#             'url': result['secure_url'],
#             'duration': result.get('duration', 0)
#         }
#     except Exception as e:
#         raise Exception(f"Cloudinary upload failed: {str(e)}")


def upload_audio(file):
    try:
        result = cloudinary.uploader.upload(
            file,
            resource_type="video",  # Cloudinary treats audio as video type
            folder=settings.CLOUDINARY['folder'],
            allowed_formats=["wav", "mp3", "webm"],
            timeout=30
        )
        return {
            'public_id': result['public_id'],
            'url': result['secure_url'],
            'duration': result.get('duration', 0)
        }
    except Exception as e:
        logger.error(f"Cloudinary upload error: {e}")
        raise Exception(f"Cloudinary upload failed: {str(e)}")    