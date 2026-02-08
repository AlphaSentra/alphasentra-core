# Render: Health Check
A Node.js service that performs scheduled health checks on Render-hosted services.
The service:
- Runs automated health checks every 14 minutes
- Supports monitoring multiple services simultaneously
- Automatically stops after 25 executions (~5.8 hours total runtime)
- Integrates with GitHub Actions for CI/CD workflows
- Deployment ID: 202602071439

## Installation

Using npm:

```sh
npm install
```

yarn:

```sh
yarn
```

## Usage

- Create a `.env` file in the root directory with the following content:

```sh
URLS=your_service_url_here
```

For multiple services, separate URLs with commas:
```sh
URLS=url1,url2,url3
```

- The script will automatically:
  - Run health checks every 14 minutes
  - Stop after 25 executions (approximately 5.8 hours total runtime)
  
- To use these environment variables in GitHub Actions:
  1. Go to your repository on GitHub
  2. Click Settings → Secrets and variables → Actions
  3. Under Repository secrets, click "New repository secret"
  4. Enter `URLS` as the name and your service URLs as the value
  5. These secrets will be available as `${{ secrets.URLS }}`

- Start the monitoring script:

With npm:
```sh
npm run start
```

With yarn:
```sh
yarn start
```

## Implementation Details

- Health checks run every 14 minutes
- Automatically stops after 25 executions (~5.8 hours total runtime)
- Designed to stay within Render's free tier limits

## License

ISC
