// Start an app (or any express instance) on an ephemeral port and return a
// base URL + a close fn. Keeps tests dependency-free (no supertest).
export async function listen(app) {
  const server = await new Promise((resolve) => {
    const s = app.listen(0, () => resolve(s));
  });
  const { port } = server.address();
  return { base: `http://127.0.0.1:${port}`, close: () => server.close() };
}
