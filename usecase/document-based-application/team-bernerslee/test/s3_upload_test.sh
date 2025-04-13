#!/bin/bash

# 설정
BUCKET_NAME="ai-hackerthon-pdf-bucket"
FILE_NAME="dummy_$(uuidgen).pdf"
REGION="ap-northeast-2"  # 필요한 리전으로 변경

# 더미 PDF 생성 (1페이지짜리 빈 PDF)
echo "%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 24 Tf
100 100 Td
(Hello PDF) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000061 00000 n 
0000000116 00000 n 
0000000213 00000 n 
trailer
<< /Root 1 0 R /Size 5 >>
startxref
319
%%EOF" > "$FILE_NAME"

# S3에 업로드
aws s3 cp "$FILE_NAME" "s3://$BUCKET_NAME/" --region "$REGION"
echo "Uploaded $FILE_NAME to s3://$BUCKET_NAME/"

# 삭제 (옵션)
aws s3 rm "s3://$BUCKET_NAME/$FILE_NAME" --region "$REGION"
echo "Deleted $FILE_NAME from s3://$BUCKET_NAME/"

# 로컬 파일도 삭제
rm "$FILE_NAME"