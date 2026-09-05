String weatherCodeToCondition(int code) {
  switch (code) {
    case 0:
      return 'Clear';
    case 1:
    case 2:
      return 'Partly Cloudy';
    case 3:
      return 'Cloudy';
    case 45:
    case 48:
      return 'Foggy';
    case 51:
    case 53:
    case 55:
      return 'Drizzle';
    case 61:
    case 63:
    case 65:
      return 'Rain';
    case 71:
    case 73:
    case 75:
      return 'Snow';
    case 80:
    case 81:
    case 82:
      return 'Rain Showers';
    case 85:
    case 86:
      return 'Snow Showers';
    case 95:
      return 'Thunderstorm';
    case 96:
    case 99:
      return 'Thunderstorm';
    default:
      return 'Unknown';
  }
}
