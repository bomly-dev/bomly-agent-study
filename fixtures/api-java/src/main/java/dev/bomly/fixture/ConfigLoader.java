package dev.bomly.fixture;

import org.apache.commons.configuration2.BaseConfiguration;
import org.apache.commons.configuration2.Configuration;

/**
 * Resolves service configuration values, including variable interpolation
 * (e.g. {@code ${host}}). commons-configuration2 performs the interpolation
 * through commons-text, which is the transitive dependency of interest here.
 */
public final class ConfigLoader {

    private final Configuration cfg = new BaseConfiguration();

    public ConfigLoader() {
        cfg.addProperty("host", "bookmarks.example.com");
        cfg.addProperty("scheme", "https");
        cfg.addProperty("baseUrl", "${scheme}://${host}/api");
    }

    public void set(String key, String value) {
        cfg.setProperty(key, value);
    }

    /** Returns the value with any ${...} references interpolated. */
    public String resolve(String key) {
        return cfg.getString(key);
    }
}
