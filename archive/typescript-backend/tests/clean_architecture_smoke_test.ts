import { buildAppContainer } from "../src/config/diContainer";

async function main() {
  const container = buildAppContainer();
  const result = await container.suggestDishController.handle("user-1");
  console.log(JSON.stringify(result, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
