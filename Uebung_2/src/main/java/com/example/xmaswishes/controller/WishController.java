package com.example.xmaswishes.controller;

import com.example.xmaswishes.model.Wish;
import com.example.xmaswishes.repository.WishRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@RestController
@RequestMapping("/api/wishes")
public class WishController {

    private static final Logger logger = LoggerFactory.getLogger(WishController.class);

    @Autowired
    private WishRepository wishRepository;

    @PostMapping
    public Wish createWish(@RequestBody Wish newWish) {
        logContainerName();
        newWish.setStatus(1);
        newWish.setCreatedAt(Instant.now());
        newWish.setUpdatedAt(Instant.now());
        return wishRepository.save(newWish);
    }

    @GetMapping
    public List<Wish> getAllWishes() {
        logContainerName();
        return wishRepository.findAll();
    }

    @GetMapping("/{id}")
    public Wish getWishById(@PathVariable Long id) {
        logContainerName();
        return wishRepository.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Wish not found"));
    }

    @PutMapping("/{id}/status/{status}")
    public Wish updateWishStatus(@PathVariable Long id, @PathVariable int status) {
        logContainerName();
        Wish wish = wishRepository.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Wish not found"));

        wish.setStatus(status);
        wish.setUpdatedAt(Instant.now());
        return wishRepository.save(wish);
    }

    @DeleteMapping("/{id}")
    public void deleteWish(@PathVariable Long id) {
        logContainerName();
        if (!wishRepository.existsById(id)) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Wish not found");
        }
        wishRepository.deleteById(id);
    }

    private void logContainerName() {
        String containerName = System.getenv("HOSTNAME");
        logger.info("Request handled by container: " + (containerName != null ? containerName : "unknown"));
    }
}
