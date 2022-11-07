#!/bin/bash

echo "Downloading topics, qrels, and runs"
mkdir -p data
cd data
git clone https://github.com/grill-lab/CODEC

cd ..
echo "Downloading CODEC (Documents Corpus)..."
wget https://codec-public-data.s3.amazonaws.com/codec_documents.jsonl -P "./data/document_corpus"

echo "Downloading kilt corpus"
mkdir -p data/kilt

echo "Downloading KILT (Entity KB)..."
wget http://dl.fbaipublicfiles.com/KILT/kilt_knowledgesource.json -P "./data/kilt"
