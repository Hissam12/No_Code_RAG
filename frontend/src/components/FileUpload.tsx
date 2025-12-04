import React, { useState } from 'react';
import axios from 'axios';
import { Upload, Loader } from 'lucide-react';

interface FileUploadProps {
    onUploadComplete: () => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onUploadComplete }) => {
    const [uploading, setUploading] = useState(false);

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            setUploading(true);

            const formData = new FormData();
            formData.append('file', file);

            try {
                await axios.post('http://localhost:8000/upload', formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                });
                onUploadComplete();
            } catch (error) {
                console.error('Upload failed:', error);
                alert('Upload failed');
            } finally {
                setUploading(false);
            }
        }
    };

    return (
        <div className="glass-panel" style={{ padding: '20px', marginBottom: '20px' }}>
            <h3 style={{ marginTop: 0 }}>Ingestion</h3>
            <label className="btn" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
                {uploading ? <Loader className="animate-spin" /> : <Upload />}
                {uploading ? 'Processing...' : 'Upload PDF/TXT'}
                <input type="file" onChange={handleFileChange} style={{ display: 'none' }} accept=".pdf,.txt" disabled={uploading} />
            </label>
        </div>
    );
};

export default FileUpload;
