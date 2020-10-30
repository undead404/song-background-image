import axios from 'axios';
import chalk from 'chalk';
import get from 'lodash/get';

const MAX_RETRIES = 5;
export default async function requestData(url, topField, retriesNumber = 0) {
  console.debug(
    chalk.yellow(`requestData(${url}, ${topField}, ${retriesNumber})`),
  );
  try {
    const { data } = await axios.get(url, {
      timeout: 1000 * 2 ** retriesNumber,
    });
    if (data.error) {
      if (data.error === 6) {
        return;
      }
      throw new Error(`Error ${data.error}: ${data.message}`);
    }
    if (!get(data, topField)) {
      console.debug(data);
      throw new Error(`Empty response`);
    }
    return data[topField];
  } catch (error) {
    console.error(chalk.red(error.message));
    if (retriesNumber >= MAX_RETRIES) {
      throw error;
    }
    return requestData(url, topField, retriesNumber + 1);
  }
}
