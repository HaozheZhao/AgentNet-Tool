import React, { useEffect, useState } from "react";

interface EditableTextProps {
    text: string;
    onSave: (newText: string) => void;
    row_character_number?: number;
    before: string;
    after: string;
    defaultText?: string;
}

const EditableText: React.FC<EditableTextProps> = ({ text, onSave, row_character_number, before, after, defaultText }) => {
    const [isEditing, setIsEditing] = useState<boolean>(false);
    const [currentText, setCurrentText] = useState<string>(text);

    const handleTextDoubleClick = () => {
        setIsEditing(true);
    };

    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setCurrentText(e.target.value);
    };

    const handleBlur = () => {
        setIsEditing(false);
        onSave(currentText);
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter") {
            setIsEditing(false);
            onSave(currentText);
        }
    };

    useEffect(() => {
        setCurrentText(text);
    }, [text]);

    return (
        <div className="w-full max-w-full">
            {isEditing ? (
                <textarea
                    rows={Math.max(2, Math.ceil((currentText?.length || 0) / (row_character_number || 40)) + 1)}
                    value={currentText}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    onKeyDown={handleKeyDown}
                    autoFocus
                    className={after}
                />
            ) : (
                <div
                    className={before}
                    onDoubleClick={handleTextDoubleClick}
                    style={{ whiteSpace: "pre-wrap", wordBreak: "break-word", overflowWrap: "break-word" }}
                >
                    {currentText && currentText.length > 0
                        ? currentText
                        : defaultText}
                </div>
            )}
        </div>
    );
};

export default EditableText;
