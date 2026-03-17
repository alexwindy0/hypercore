"""
Cloudinary Service - Handle image uploads and management
"""
import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask import current_app

class CloudinaryService:
    """Service for Cloudinary image management"""
    
    def __init__(self):
        self.cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
        self.api_key = os.getenv('CLOUDINARY_API_KEY')
        self.api_secret = os.getenv('CLOUDINARY_API_SECRET')
        
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True
        )
        
        self.folder = 'hypercore/products'
    
    def upload_image(self, file, folder=None, public_id=None, transformation=None):
        """
        Upload an image to Cloudinary
        
        Args:
            file: File to upload (FileStorage or file path)
            folder: Cloudinary folder (default: hypercore/products)
            public_id: Custom public ID
            transformation: Image transformation options
        
        Returns:
            dict: Upload result with URL and public_id
        """
        upload_folder = folder or self.folder
        
        upload_options = {
            'folder': upload_folder,
            'resource_type': 'image',
            'allowed_formats': ['jpg', 'jpeg', 'png', 'gif', 'webp'],
            'max_file_size': 2097152,  # 2MB
        }
        
        if public_id:
            upload_options['public_id'] = public_id
        
        # Default transformation for product images
        if transformation:
            upload_options['transformation'] = transformation
        else:
            upload_options['transformation'] = [
                {'width': 1200, 'height': 1200, 'crop': 'limit'},  # Max dimensions
                {'quality': 'auto:good', 'fetch_format': 'auto'}   # Auto-optimize
            ]
        
        try:
            # Handle Flask FileStorage
            if hasattr(file, 'read'):
                file.seek(0)
                result = cloudinary.uploader.upload(file, **upload_options)
            else:
                # Handle file path
                result = cloudinary.uploader.upload(file, **upload_options)
            
            return {
                'success': True,
                'url': result['secure_url'],
                'public_id': result['public_id'],
                'width': result.get('width'),
                'height': result.get('height'),
                'format': result.get('format'),
                'bytes': result.get('bytes')
            }
        except cloudinary.exceptions.Error as e:
            current_app.logger.error(f"Cloudinary upload error: {str(e)}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            current_app.logger.error(f"Unexpected upload error: {str(e)}")
            return {'success': False, 'error': 'Upload failed'}
    
    def upload_multiple(self, files, folder=None):
        """
        Upload multiple images
        
        Args:
            files: List of files to upload
            folder: Cloudinary folder
        
        Returns:
            list: List of upload results
        """
        results = []
        for file in files:
            result = self.upload_image(file, folder=folder)
            results.append(result)
        return results
    
    def delete_image(self, public_id):
        """
        Delete an image from Cloudinary
        
        Args:
            public_id: Public ID of the image
        
        Returns:
            dict: Deletion result
        """
        try:
            result = cloudinary.uploader.destroy(public_id)
            return {
                'success': result.get('result') == 'ok',
                'result': result
            }
        except cloudinary.exceptions.Error as e:
            current_app.logger.error(f"Cloudinary delete error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def delete_multiple(self, public_ids):
        """
        Delete multiple images
        
        Args:
            public_ids: List of public IDs
        
        Returns:
            dict: Batch deletion result
        """
        try:
            result = cloudinary.api.delete_resources(public_ids)
            return {
                'success': True,
                'deleted': result.get('deleted', {}),
                'partial': result.get('partial', False)
            }
        except cloudinary.exceptions.Error as e:
            current_app.logger.error(f"Cloudinary batch delete error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_image_url(self, public_id, transformation=None):
        """
        Get URL for an image with optional transformation
        
        Args:
            public_id: Public ID of the image
            transformation: Transformation options
        
        Returns:
            str: Image URL
        """
        if transformation:
            return cloudinary.CloudinaryImage(public_id).build_url(**transformation)
        return cloudinary.CloudinaryImage(public_id).build_url()
    
    def generate_thumbnail(self, public_id, width=300, height=300, crop='fill'):
        """
        Generate thumbnail URL
        
        Args:
            public_id: Public ID of the image
            width: Thumbnail width
            height: Thumbnail height
            crop: Crop mode
        
        Returns:
            str: Thumbnail URL
        """
        transformation = {
            'width': width,
            'height': height,
            'crop': crop,
            'quality': 'auto'
        }
        return self.get_image_url(public_id, transformation)
    
    def list_images(self, folder=None, max_results=100):
        """
        List images in a folder
        
        Args:
            folder: Folder to list
            max_results: Maximum results
        
        Returns:
            dict: List of images
        """
        list_folder = folder or self.folder
        
        try:
            result = cloudinary.api.resources(
                type='upload',
                prefix=list_folder,
                max_results=max_results
            )
            return {
                'success': True,
                'resources': result.get('resources', [])
            }
        except cloudinary.exceptions.Error as e:
            current_app.logger.error(f"Cloudinary list error: {str(e)}")
            return {'success': False, 'error': str(e)}

# Singleton instance
cloudinary_service = CloudinaryService()
