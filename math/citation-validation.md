# Citation validation

The model may only reference IDs in the retrieved evidence set. Reject the whole response if it is not grounded, any claim has blank text, any claim lacks IDs, or any ID is unknown. The API derives excerpt, kind, segment ID, start, and end from stored evidence rows. If output fails validation or retrieval returns no rows, persist an explicit insufficient-evidence answer without citations.
