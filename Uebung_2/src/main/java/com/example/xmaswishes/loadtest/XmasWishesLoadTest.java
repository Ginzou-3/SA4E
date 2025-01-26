package com.example.xmaswishes.loadtest;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.concurrent.atomic.AtomicLong;

public class XmasWishesLoadTest {

    // The base URL of your XmasWishes REST API
    private static final String BASE_URL = "http://localhost:8080/api/wishes";

    // Tweak concurrency + requests as needed
    private static final int THREADS = 10;
    private static final int REQUESTS_PER_THREAD = 10;

    public static void main(String[] args) throws InterruptedException {
        // These counters will track how many requests are successful vs. errors
        AtomicLong successCount = new AtomicLong();
        AtomicLong errorCount   = new AtomicLong();

        long startTime = System.currentTimeMillis();

        // Create and start multiple threads
        Thread[] threads = new Thread[THREADS];
        for (int i = 0; i < THREADS; i++) {
            threads[i] = new Thread(() -> {
                // Each thread creates its own HttpClient instance
                HttpClient client = HttpClient.newBuilder()
                        .connectTimeout(Duration.ofSeconds(5))
                        .build();
                ObjectMapper mapper = new ObjectMapper();

                for (int j = 0; j < REQUESTS_PER_THREAD; j++) {
                    // Build the JSON body (a WishDTO-like object)
                    WishDTO wish = new WishDTO("Tester", "I want a surprise!", 1);
                    try {
                        String jsonBody = mapper.writeValueAsString(wish);

                        // Build the POST request
                        HttpRequest request = HttpRequest.newBuilder()
                                .uri(URI.create(BASE_URL))
                                .header("Content-Type", "application/json")
                                .POST(HttpRequest.BodyPublishers.ofString(jsonBody))
                                .build();

                        // Send the request and parse the response
                        HttpResponse<String> response = client.send(request,
                                HttpResponse.BodyHandlers.ofString());

                        int statusCode = response.statusCode();
                        if (statusCode >= 200 && statusCode < 300) {
                            successCount.incrementAndGet();
                        } else {
                            errorCount.incrementAndGet();
                            System.err.println("Received status code: " + statusCode);
                        }
                    } catch (IOException | InterruptedException e) {
                        errorCount.incrementAndGet();
                        e.printStackTrace();
                    }
                }
            });
        }

        // Start all threads
        for (Thread t : threads) {
            t.start();
        }

        // Wait for all threads to finish
        for (Thread t : threads) {
            t.join();
        }

        long endTime = System.currentTimeMillis();
        double totalTimeSec = (endTime - startTime) / 1000.0;

        long totalRequests = successCount.get() + errorCount.get();
        double rps         = successCount.get() / totalTimeSec;

        // Print summary
        System.out.println("Total Requests:  " + totalRequests);
        System.out.println("Successful:      " + successCount.get());
        System.out.println("Errors:          " + errorCount.get());
        System.out.printf("Time (seconds):  %.2f%n", totalTimeSec);
        System.out.printf("Requests/sec:    %.2f%n", rps);
    }

    // Simple DTO class for JSON body
    static class WishDTO {
        public String personName;
        public String wishText;
        public int status;

        // Constructors, getters, setters, etc.
        public WishDTO() {}
        public WishDTO(String personName, String wishText, int status) {
            this.personName = personName;
            this.wishText = wishText;
            this.status = status;
        }
    }
}
