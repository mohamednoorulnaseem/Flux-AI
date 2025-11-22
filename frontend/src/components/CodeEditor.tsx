// frontend/src/components/CodeEditor.tsx
import Editor from "@monaco-editor/react";

type CodeEditorProps = {
  code: string;
  language: string;
  onChange: (value: string) => void;
};

const CodeEditor: React.FC<CodeEditorProps> = ({
  code,
  language,
  onChange,
}) => {
  return (
    <div className="editor-wrapper">
      <Editor
        height="420px"
        language={language}
        value={code}
        theme="vs-dark"
        onChange={(value) => onChange(value ?? "")}
        options={{
          fontSize: 14,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          glyphMargin: true,
          smoothScrolling: true,
          automaticLayout: true,
        }}
      />
    </div>
  );
};

export default CodeEditor;
