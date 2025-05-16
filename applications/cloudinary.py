import cloudinary
import cloudinary.uploader
from django.conf import settings

# Configure Cloudinary
cloudinary.config(**settings.CLOUDINARY)

def upload_video(file):
    """Upload video file to Cloudinary"""
    try:
        result = cloudinary.uploader.upload(
            file,
            resource_type="video",
            folder="interview_videos",
            # folder=settings.CLOUDINARY['folder'],
            allowed_formats=["webm", "mp4"],
            timeout=120
        )
        return   result
        #  {
           
            # 'public_id': result['public_id'],
            # 'url': result['secure_url'],
            # 'duration': result.get('duration', 0)
        # }
    except Exception as e:
        raise Exception(f"Cloudinary upload failed: {str(e)}")