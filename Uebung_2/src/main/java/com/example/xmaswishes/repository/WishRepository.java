package com.example.xmaswishes.repository;

import com.example.xmaswishes.model.Wish;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface WishRepository extends JpaRepository<Wish, Long> {
    // Additional custom queries if needed
}