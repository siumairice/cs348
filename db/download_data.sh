#!/usr/bin/env bash
# Download the production dataset: the latest Rebrickable CSV export.
# Usage: db/download_data.sh [destination]   (default: data)
#
# Rebrickable publishes these at https://rebrickable.com/downloads/ and
# regenerates them daily, so row counts grow over time. db/import_data.py
# checks every file's header before loading, so a format change fails loudly.
set -euo pipefail

DEST="${1:-data}"
BASE_URL="https://cdn.rebrickable.com/media/downloads"
FILES=(
  themes sets colors part_categories parts part_relationships elements
  minifigs inventories inventory_parts inventory_sets inventory_minifigs
  color_mappings part_mappings set_mappings
)

mkdir -p "$DEST"
for name in "${FILES[@]}"; do
  echo "Downloading $name.csv"
  # Write to a temp file first so a failed download never leaves a truncated CSV.
  curl -fsSL "$BASE_URL/$name.csv.gz" | gunzip > "$DEST/$name.csv.tmp"
  mv "$DEST/$name.csv.tmp" "$DEST/$name.csv"
done
echo "Saved ${#FILES[@]} CSV files to $DEST/"
